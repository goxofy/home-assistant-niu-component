# Home Assistant NIU 滑板车集成

这是一个用于Home Assistant的自定义组件，用于集成NIU电动滑板车。

## 功能特点

- **UI配置**: 通过Home Assistant的集成界面进行现代化UI配置
- **多种传感器**: 监控电池状态、位置、速度等
- **实时更新**: 从您的NIU滑板车获取实时数据
- **多滑板车支持**: 支持一个账户中的多辆滑板车
- **可配置传感器**: 选择要监控的传感器

## 安装

### 方法一：HACS（推荐）

1. 在HACS中添加此仓库：
   - 进入HACS → 集成
   - 点击"+"按钮
   - 搜索"NIU Scooter Integration"
   - 点击"下载"

2. 重启Home Assistant

3. 进入设置 → 设备与服务 → 集成
4. 点击"+"按钮并搜索"NIU Scooter Integration"
5. 按照设置向导操作

### 方法二：手动安装

1. 下载此仓库
2. 将`custom_components/niu`文件夹复制到您的Home Assistant `config/custom_components/`目录
3. 重启Home Assistant
4. 进入设置 → 设备与服务 → 集成
5. 点击"+"按钮并搜索"NIU Scooter Integration"
6. 按照设置向导操作

## 配置

### UI配置（推荐）

1. 进入设置 → 设备与服务 → 集成
2. 点击"+"按钮并搜索"NIU Scooter Integration"
3. 输入您的NIU账户凭据：
   - **用户名/邮箱**: 您的NIU账户用户名或邮箱
   - **密码**: 您的NIU账户密码
   - **滑板车ID**: 要监控的滑板车ID（默认：0）
4. 选择要监控的传感器
5. 点击"提交"

### 旧版YAML配置（已弃用）

如果您正在从旧版本升级，可以临时使用YAML配置：

```yaml
# configuration.yaml

sensor:
  - platform: niu
    username: user@example.com
    password: mysecretpassword
    scooter_id: 0
    monitored_variables:
      - BatteryCharge          # 电池
      - Isconnected            # 电池
      - TimesCharged           # 电池
      - temperatureDesc        # 电池
      - Temperature            # 电池
      - BatteryGrade           # 电池
      - CurrentSpeed           # 电机
      - ScooterConnected       # 电机（包含经纬度属性，可用于地图显示）
      - IsCharging             # 电机
      - IsLocked               # 电机
      - TimeLeft               # 电机
      - EstimatedMileage       # 电机
      - centreCtrlBatt         # 电机
      - HDOP                   # 电机
      - Longitude              # 电机
      - Latitude               # 电机
      - totalMileage           # 总体
      - DaysInUse              # 总体
      - Distance               # 距离
      - RidingTime             # 距离
      - LastTrackStartTime     # 最后行程
      - LastTrackEndTime       # 最后行程
      - LastTrackDistance      # 最后行程
      - LastTrackAverageSpeed  # 最后行程
      - LastTrackRidingtime    # 最后行程
      - LastTrackThumb         # 最后行程
```

## 可用传感器

### 电池传感器
- **BatteryCharge**: 当前电池百分比
- **Isconnected**: 连接状态
- **TimesCharged**: 充电次数
- **temperatureDesc**: 温度描述
- **Temperature**: 电池温度
- **BatteryGrade**: 电池健康等级

### 电机传感器
- **CurrentSpeed**: 当前速度
- **ScooterConnected**: 滑板车连接状态
- **IsCharging**: 充电状态
- **IsLocked**: 锁定状态
- **TimeLeft**: 预估剩余时间
- **EstimatedMileage**: 预估剩余里程
- **centreCtrlBatt**: 中央控制器电池
- **HDOP**: GPS精度

### 位置传感器
- **Longitude**: GPS经度
- **Latitude**: GPS纬度

### 统计传感器
- **totalMileage**: 总里程
- **DaysInUse**: 使用天数
- **Distance**: 距离
- **RidingTime**: 骑行时间

### 行程传感器
- **LastTrackStartTime**: 最后行程开始时间
- **LastTrackEndTime**: 最后行程结束时间
- **LastTrackDistance**: 最后行程距离
- **LastTrackAverageSpeed**: 最后行程平均速度
- **LastTrackRidingtime**: 最后行程骑行时间
- **LastTrackThumb**: 最后行程缩略图

## 多滑板车支持

如果您拥有多辆滑板车，可以多次添加集成：
1. 进入设置 → 设备与服务 → 集成
2. 点击"+"按钮并搜索"NIU Scooter Integration"
3. 输入相同的凭据但使用不同的**滑板车ID**
4. 为每辆滑板车重复此操作

## 故障排除

### 连接问题
- 验证您的NIU账户凭据
- 检查您的网络连接
- 确保NIU应用在您的手机上正常工作

### 传感器问题
- 某些传感器可能因滑板车型号而异
- 尝试重启Home Assistant
- 检查日志中的错误消息

### 固件问题
- 确保您的滑板车有最新的固件
- 某些功能需要特定的固件版本

## 已知问题

- 集成需要稳定的网络连接
- 如果滑板车离线，某些传感器可能不会更新
- 当滑板车静止时，GPS数据可能有限

## 支持

- **问题反馈**: [GitHub Issues](https://github.com/goxofy/home-assistant-niu-component/issues)
- **文档**: [GitHub 仓库](https://github.com/goxofy/home-assistant-niu-component)

## 更新日志

### 版本 2.0.0
- **新增**: 基于UI的配置
- **新增**: 现代集成架构
- **新增**: 数据协调器，提升性能
- **新增**: 改进的错误处理
- **新增**: 更好的传感器验证
- **改进**: 代码结构和可维护性
- **弃用**: YAML配置（仍支持迁移）

### 版本 1.0.2
- 错误修复和改进
- 更好的错误处理
- 多滑板车支持

## 许可证

本项目采用MIT许可证 - 详情请参阅[LICENSE](LICENSE)文件。

