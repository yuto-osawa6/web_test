from fastapi import FastAPI
import pandas as pd
from pandas.tseries.offsets import MonthEnd
from pathlib import Path
from fastapi.responses import JSONResponse
from datetime import datetime


app = FastAPI()
csv_dir = Path("app/csv/sample_log.csv")

@app.get("/read_csv_file/")
async def read_csv_file():
    try:
        # # CSVファイルを読み込む（headerを指定して列名を振る）
        df = pd.read_csv(csv_dir, header=None, names=["会員ID", "コース", "アクション", "日時"])
        df["日時"] = pd.to_datetime(df["日時"])

        # 終了日時の追加
        result = df.groupby(['会員ID', 'コース']).apply(lambda group: group.assign(
            終了日時=group['日時'].shift(-1)
        )).reset_index(drop=True)

        # 終了日時を月の最後に設定
        result['終了日時'] = result['終了日時'].fillna(datetime.now())
        result['終了日時'] = pd.to_datetime(result["終了日時"] + MonthEnd(0))
        result['終了日時'] = result['終了日時'].apply(lambda x: x.replace(hour=23, minute=59, second=59))

        # 日時の範囲を確認して統合
        merged_data = []
        current_range = None

        for index, row in result[result["アクション"] == 1].sort_values(by=["会員ID", "日時"]).iterrows():
          if current_range is None or current_range['会員ID'] != row['会員ID'] or current_range['終了日時'] < row['日時']:
              if current_range is not None:
                  merged_data.append(current_range)
              current_range = {'会員ID': row['会員ID'], 'アクション': row['アクション'], '日時': row['日時'], '終了日時': row['終了日時']}
          else:
              current_range['終了日時'] = max(current_range['終了日時'], row['終了日時'])

        # リストをPandasデータフレームに変換
        merged_df = pd.DataFrame(merged_data)
        # # 条件
        start_date_condition = merged_df["日時"] < "2020-01-01 00:00:00"
        end_date_condition = merged_df["終了日時"] > "2020-04-01 00:00:00"
        filtered_ids = merged_df.loc[start_date_condition & end_date_condition, "会員ID"].unique()
        result = {"会員ID": list(map(str, filtered_ids))}
        return JSONResponse(content=result)
    except Exception as e:
        # エラーが発生した場合はエラーメッセージを返す
        return {"error": str(e)}

# 結果
# {"会員ID":["337","408","438","515","681","794","965","1466","2003","2146","2400","2548","2573"
#         ,"2703","2725","2840","2878","2926","3260","3290","3394","3442","3903","3939","4025","4149","4375","4500",
#         "4908","5038","5161","5497","5544","5820","6064","6129","6337","6458","6638","6823","6986","8873",
#         "8914","9000","9029","9583","9619","9699","9951"]}