import pandas as pd
from app.core.config import influx_client, INFLUX_BUCKET

class InfluxRepository:
    def get_topology_data(self) -> list:
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -30d)
          |> filter(fn: (r) => r["_measurement"] == "mqtt_consumer")
          |> keep(columns: ["fan_id", "location", "_field"])
          |> group(columns: ["fan_id", "location", "_field"])
          |> distinct(column: "_field")
        '''
        query_api = influx_client.query_api()
        return query_api.query(query)

    def get_recent_data(self, fan_id: str, minutes: int = 1440) -> pd.DataFrame:
        query = f'''
        from(bucket: "{INFLUX_BUCKET}")
          |> range(start: -{minutes}m)
          |> filter(fn: (r) => r["fan_id"] == "{fan_id}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> group()
          |> sort(columns: ["_time"])
          |> tail(n: 300)
        '''
        query_api = influx_client.query_api()
        result = query_api.query_data_frame(query)

        if isinstance(result, list):
            if not result:
                return pd.DataFrame()
            return pd.concat(result, ignore_index=True)
        return result