# deployment filter query

MATCH (ds:Datasheet)<-[:TRAINED_ON]-(mc:ModelCard)-[:Deployed_On]->(depl:Deployment)-[:On_Device_Type]->(device:EdgeDevice)
WHERE ds.external_id = "https://archive.ics.uci.edu/dataset/2/adult"
  AND device.name = "jetson-nano"
  AND depl.start_time >= datetime({ year: 2024, month: 1, day: 1 }) - duration({ months: 1 })
  AND depl.mean_accuracy >= 0.8
  AND depl.power_consumption_average_watts < 30
RETURN mc
ORDER BY depl.mean_accuracy DESC, depl.power_consumption_average_watts ASC




MATCH (ds:Datasheet)<-[:TRAINED_ON]-(mc:ModelCard)-[:Deployed_On]->(depl:Deployment)-[:On_Device_Type]->(device:EdgeDevice)
WHERE ds.external_id = "https://archive.ics.uci.edu/dataset/2/adult"
AND device.external_id="jetson-nano"
AND depl.power_consumption_average_watts < 50

RETURN mc, depl