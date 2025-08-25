"""Constants for the NIU integration."""

DOMAIN = "niu"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCOOTER_ID = "scooter_id"
CONF_MONITORED_VARIABLES = "monitored_variables"

DEFAULT_SCOOTER_ID = 0
DEFAULT_MONITORED_VARIABLES = ["BatteryCharge"]

# API URLs
ACCOUNT_BASE_URL = "https://account.niu.com"
LOGIN_URI = "/v3/api/oauth2/token"
API_BASE_URL = "https://app-api.niu.com"
MOTOR_BATTERY_API_URI = "/v3/motor_data/battery_info"
MOTOR_INDEX_API_URI = "/v5/scooter/motor_data/index_info"
MOTOINFO_LIST_API_URI = "/v5/scooter/list"
MOTOINFO_ALL_API_URI = "/motoinfo/overallTally"
TRACK_LIST_API_URI = "/v5/track/list/v2"

# Sensor types
SENSOR_TYPE_BAT = "BAT"
SENSOR_TYPE_MOTO = "MOTO"
SENSOR_TYPE_DIST = "DIST"
SENSOR_TYPE_OVERALL = "TOTAL"
SENSOR_TYPE_POS = "POSITION"
SENSOR_TYPE_TRACK = "TRACK"

# Available sensors
AVAILABLE_SENSORS = [
    "BatteryCharge",
    "Isconnected",
    "TimesCharged",
    "temperatureDesc",
    "Temperature",
    "BatteryGrade",
    "CurrentSpeed",
    "ScooterConnected",
    "IsCharging",
    "IsLocked",
    "TimeLeft",
    "EstimatedMileage",
    "centreCtrlBatt",
    "HDOP",
    "Longitude",
    "Latitude",
    "Distance",
    "RidingTime",
    "totalMileage",
    "DaysInUse",
    "LastTrackStartTime",
    "LastTrackEndTime",
    "LastTrackDistance",
    "LastTrackAverageSpeed",
    "LastTrackRidingtime",
    "LastTrackThumb",
]

# Chinese sensor names for UI display
SENSOR_NAMES_ZH = {
    "BatteryCharge": "电池电量",
    "Isconnected": "连接状态",
    "TimesCharged": "充电次数",
    "temperatureDesc": "温度描述",
    "Temperature": "电池温度",
    "BatteryGrade": "电池等级",
    "CurrentSpeed": "当前速度",
    "ScooterConnected": "滑板车连接",
    "IsCharging": "充电状态",
    "IsLocked": "锁定状态",
    "TimeLeft": "剩余时间",
    "EstimatedMileage": "预估里程",
    "centreCtrlBatt": "中央控制器电池",
    "HDOP": "GPS精度",
    "Longitude": "经度",
    "Latitude": "纬度",
    "Distance": "距离",
    "RidingTime": "骑行时间",
    "totalMileage": "总里程",
    "DaysInUse": "使用天数",
    "LastTrackStartTime": "最后行程开始时间",
    "LastTrackEndTime": "最后行程结束时间",
    "LastTrackDistance": "最后行程距离",
    "LastTrackAverageSpeed": "最后行程平均速度",
    "LastTrackRidingtime": "最后行程骑行时间",
    "LastTrackThumb": "最后行程缩略图",
}
