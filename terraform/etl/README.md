Perform basic ETL

```
aws s3 cp sample_pnl.csv s3://pnl-raw-data-108300c39dacb6a734cad63bb2/sample_pnl.csv
```

```
aws athena start-query-execution \
  --query-string "SELECT desk_id, total_net_pnl, var_95, risk_flag FROM risk_pnl_db.desk_risk_summaries WHERE risk_flag = true;" \
  --work-group "risk_analytics_workgroup"
```

```
aws athena get-query-results --query-execution-id 3af37271-e18b-462a-aa9d-e30387e3b0aa
```
