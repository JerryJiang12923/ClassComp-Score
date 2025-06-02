# app.py
import os
from flask import Flask, request, jsonify, render_template, url_for, send_file
from flask_cors import CORS
from datetime import datetime
import pandas as pd
import pytz

# 从 db.py 获取连接池接口
from db import get_conn, put_conn

app = Flask(__name__)
CORS(app)

# 导出目录（可通过环境变量覆盖）
EXPORT_FOLDER = os.getenv("EXPORT_FOLDER", "exports")
os.makedirs(EXPORT_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit_scores", methods=["POST"])
def submit_scores():
    try:
        data = request.get_json()
        if not data:
            return jsonify(success=False, message="无效的请求数据"), 400

        required_fields = ["name", "info_class", "checked_grade", "scores"]
        if not all(field in data for field in required_fields):
            return jsonify(success=False, message="缺少必要字段"), 400

        conn = get_conn()
        cur = conn.cursor()

        insert_sql = """
            INSERT INTO public.scores (
                评分人姓名,
                信息委员班级,
                被查年级,
                被查班级,
                分项1,
                分项2,
                分项3,
                总分,
                备注
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for score_data in data["scores"]:
            cur.execute(
                insert_sql,
                (
                    data["name"],
                    data["info_class"],
                    data["checked_grade"],
                    score_data["className"],
                    score_data["score1"],
                    score_data["score2"],
                    score_data["score3"],
                    score_data.get("total", 0),
                    score_data.get("note", ""),
                ),
            )

        conn.commit()
        put_conn(conn)

        return (
            jsonify(success=True, redirect=url_for("success")),
            200,
            {"Content-Type": "application/json"},
        )

    except Exception as e:
        try:
            put_conn(conn)
        except:
            pass
        return jsonify(success=False, message=str(e)), 500

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/export_excel")
def export_excel():
    month = request.args.get("month")
    if not month:
        return "请提供 month=YYYY-MM 查询参数", 400

    try:
        conn = get_conn()
        cur = conn.cursor()

        sql = """
            SELECT
              id,
              评分人姓名,
              信息委员班级,
              被查年级,
              被查班级,
              分项1,
              分项2,
              分项3,
              总分,
              备注,
              提交时间
            FROM public.scores
            WHERE to_char(提交时间, 'YYYY-MM') = %s
            ORDER BY 提交时间
        """
        cur.execute(sql, (month,))
        rows = cur.fetchall()
        put_conn(conn)

        if not rows:
            return "当月无数据", 200

        df = pd.DataFrame(rows)
        df["提交时间"] = pd.to_datetime(df["提交时间"], utc=True)
        df["提交时间"] = df["提交时间"].dt.tz_convert("Asia/Shanghai").dt.tz_localize(None)

        df["周"] = df["提交时间"].dt.isocalendar().week
        weeks = sorted(df["周"].unique())
        week_bins = [weeks[i : i + 2] for i in range(0, len(weeks), 2)]
        week_labels = [f"第{i+1}段" for i in range(len(week_bins))]

        df["周期"] = None
        for label, bins in zip(week_labels, week_bins):
            df.loc[df["周"].isin(bins), "周期"] = label

        filename = f"评分表_{month.replace('-', '')}.xlsx"
        filepath = os.path.join(EXPORT_FOLDER, filename)

        with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
            for label in week_labels:
                grp_cycle = df[df["周期"] == label]
                if grp_cycle.empty:
                    continue
                for grade, g_df in grp_cycle.groupby("被查年级"):
                    pivot = g_df.pivot_table(
                        index="信息委员班级",
                        columns="被查班级",
                        values="总分",
                        aggfunc="mean",
                    )
                    pivot.loc["平均分"] = pivot.mean()
                    sheet_name = f"{label}-{grade}"[:31]
                    pivot.to_excel(writer, sheet_name=sheet_name)

            summary = (
                df.groupby("被查班级")["总分"]
                .mean()
                .reset_index()
                .rename(columns={"总分": "平均分"})
            )
            summary.to_excel(writer, sheet_name="汇总", index=False)

            detail_cols = [
                "id", "评分人姓名", "信息委员班级", "被查年级", "被查班级", 
                "分项1", "分项2", "分项3", "总分", "备注", "提交时间",
            ]
            df[detail_cols].to_excel(writer, sheet_name="提交明细", index=False)

        # 生成完毕后，返回文件供前端下载
        return send_file(filepath, as_attachment=True, download_name=filename)

    except Exception as e:
        try:
            put_conn(conn)
        except:
            pass
        return f"导出失败：{str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
