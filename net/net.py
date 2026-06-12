"""
一键式网络库 - WiFi + 蓝牙
带错误恢复功能
"""
import network
import time
import ubinascii
import bluetooth
from micropython import const

# ========== WiFi部分 ==========
_wifi = network.WLAN(network.STA_IF)
_ap = network.WLAN(network.AP_IF)

def wifi_reset():
    """完全重置WiFi模块"""
    global _wifi
    try:
        _wifi.active(False)
        time.sleep(0.5)
        _wifi = network.WLAN(network.STA_IF)
        time.sleep(0.1)
        return True
    except:
        return False

def wifi(ssid, password=None):
    """
    一键连接WiFi（带错误恢复）
    自动处理：重置、开启、连接、等待
    直接返回：True(成功) 或 False(失败)
    """
    global _wifi
    
    # 先关闭WiFi，重置状态
    try:
        _wifi.active(False)
        time.sleep(0.5)
        _wifi = network.WLAN(network.STA_IF)
    except:
        pass
    
    # 开启WiFi
    _wifi.active(True)
    time.sleep(0.5)
    
    # 连接WiFi
    if password:
        _wifi.connect(ssid, password)
    else:
        _wifi.connect(ssid)
    
    # 等待连接，最多15秒
    for i in range(30):
        if _wifi.isconnected():
            return True
        time.sleep(0.5)
    
    return False

def ip():
    """获取IP地址"""
    try:
        if _wifi.isconnected():
            return _wifi.ifconfig()[0]
    except:
        pass
    return "0.0.0.0"

def scan():
    """扫描WiFi（带错误恢复）"""
    try:
        _wifi.active(False)
        time.sleep(0.3)
        _wifi.active(True)
        time.sleep(0.5)
        
        networks = _wifi.scan()
        
        result = []
        for net in networks:
            ssid = net[0].decode() if net[0] else "隐藏网络"
            signal = net[3]
            if signal > -50:
                icon = "📶📶📶"
            elif signal > -70:
                icon = "📶📶"
            else:
                icon = "📶"
            result.append(f"{icon} {ssid} ({signal}dBm)")
        
        return result
    except Exception as e:
        print(f"扫描失败: {e}")
        return []

def disconnect():
    """断开WiFi"""
    try:
        _wifi.active(False)
        return True
    except:
        return False

def ap(ssid="ESP32-S3", password=None):
    """开启热点"""
    try:
        # 确保热点关闭状态
        _ap.active(False)
        time.sleep(0.3)
        
        # 开启并配置
        _ap.active(True)
        time.sleep(0.3)
        
        if password and len(password) >= 8:
            _ap.config(essid=ssid, password=password, authmode=network.AUTH_WPA_WPA2_PSK)
        else:
            _ap.config(essid=ssid, authmode=network.AUTH_OPEN)
        
        return _ap.ifconfig()[0]
    except Exception as e:
        print(f"开启热点失败: {e}")
        return False

def ap_off():
    """关闭热点"""
    try:
        _ap.active(False)
        return True
    except:
        return False

def ap_clients():
    """获取连接的设备数"""
    try:
        if _ap.active():
            return len(_ap.status('stations'))
    except:
        pass
    return 0

# ========== 蓝牙部分 ==========
_ble = None
_ble_connected = False
_ble_data = None
_ble_scan_results = []
_ble_scan_done = False
_ble_initialized = False

# 蓝牙UUID
_CUSTOM_SERVICE_UUID = bluetooth.UUID("12345678-1234-5678-1234-56789ABCDEF0")
_CUSTOM_CHAR_UUID = bluetooth.UUID("ABCD1234-1234-5678-1234-56789ABCDEF0")

# 蓝牙事件常量
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)

def _ble_irq_handler(event, data):
    """蓝牙事件处理"""
    global _ble_connected, _ble_data, _ble_scan_results, _ble_scan_done
    
    if event == _IRQ_CENTRAL_CONNECT:
        _ble_connected = True
        print("🔵 蓝牙已连接")
        
    elif event == _IRQ_CENTRAL_DISCONNECT:
        _ble_connected = False
        print("🔵 蓝牙已断开")
        
    elif event == _IRQ_GATTS_WRITE:
        conn_handle, value_handle = data
        _ble_data = _ble.gatts_read(value_handle)
        
    elif event == _IRQ_SCAN_RESULT:
        addr_type, addr, adv_type, rssi, adv_data = data
        _ble_scan_results.append({
            'mac': ubinascii.hexlify(addr).decode(),
            'rssi': rssi
        })
        
    elif event == _IRQ_SCAN_DONE:
        _ble_scan_done = True

def ble_init():
    """初始化蓝牙"""
    global _ble, _ble_initialized
    try:
        if _ble is None:
            _ble = bluetooth.BLE()
        _ble.active(False)
        time.sleep(0.2)
        _ble.irq(_ble_irq_handler)
        _ble_initialized = True
        return True
    except Exception as e:
        print(f"蓝牙初始化失败: {e}")
        return False

def ble(name="ESP32-S3"):
    """开启蓝牙广播"""
    global _ble
    
    if not _ble_initialized:
        if not ble_init():
            return False
    
    try:
        _ble.active(False)
        time.sleep(0.2)
        _ble.active(True)
        time.sleep(0.2)
        
        # 注册服务
        services = (
            (_CUSTOM_SERVICE_UUID, (
                (_CUSTOM_CHAR_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_WRITE | bluetooth.FLAG_NOTIFY),
            )),
        )
        
        try:
            ((_tx_handle, _rx_handle),) = _ble.gatts_register_services(services)
        except:
            pass
        
        # 设置名称并广播
        _ble.config(gap_name=name)
        adv_data = b'\x02\x01\x06' + bytes([len(name)+1, 0x09]) + name.encode()
        _ble.gap_advertise(100000, adv_data=adv_data)
        
        print(f"🔵 蓝牙已开启: {name}")
        return True
    except Exception as e:
        print(f"蓝牙开启失败: {e}")
        return False

def ble_off():
    """关闭蓝牙"""
    global _ble_connected
    try:
        if _ble:
            _ble.active(False)
        _ble_connected = False
        return True
    except:
        return False

def ble_send(data):
    """发送蓝牙数据"""
    if not _ble_connected:
        return False
    try:
        if isinstance(data, str):
            data = data.encode()
        return True
    except:
        return False

def ble_receive():
    """接收蓝牙数据"""
    global _ble_data
    data = _ble_data
    _ble_data = None
    return data

def ble_scan(timeout=3000):
    """扫描蓝牙设备"""
    global _ble_scan_results, _ble_scan_done
    
    if not _ble_initialized:
        if not ble_init():
            return []
    
    _ble_scan_results = []
    _ble_scan_done = False
    
    try:
        _ble.gap_scan(2000, 30000, 30000)
        
        start = time.ticks_ms()
        while not _ble_scan_done and time.ticks_diff(time.ticks_ms(), start) < timeout:
            time.sleep_ms(100)
    except Exception as e:
        print(f"扫描失败: {e}")
    
    return _ble_scan_results

def ble_connect(mac):
    """连接蓝牙设备"""
    try:
        addr = bytes.fromhex(mac)
        _ble.gap_connect(0, addr, 0x01)
        time.sleep(2)
        return True
    except:
        return False

def ble_status():
    """查看蓝牙状态"""
    return {
        'active': _ble.active() if _ble else False,
        'connected': _ble_connected
    }

# ========== 工具函数 ==========
def get_mac():
    """获取MAC地址"""
    try:
        import ubinascii
        mac = _wifi.config('mac')
        mac_str = ubinascii.hexlify(mac).decode()
        return ':'.join(mac_str[i:i+2] for i in range(0, 12, 2))
    except:
        return "00:00:00:00:00:00"

def status():
    """查看所有状态"""
    print("\n" + "=" * 40)
    print("网络状态")
    print("=" * 40)
    
    try:
        print(f"WiFi连接: {'✅' if _wifi.isconnected() else '❌'}")
        if _wifi.isconnected():
            print(f"  IP地址: {_wifi.ifconfig()[0]}")
    except:
        print(f"WiFi连接: ❌")
    
    try:
        print(f"热点状态: {'✅' if _ap.active() else '❌'}")
        if _ap.active():
            print(f"  连接设备: {ap_clients()}台")
    except:
        print(f"热点状态: ❌")
    
    try:
        ble_stat = ble_status()
        print(f"蓝牙状态: {'✅' if ble_stat['active'] else '❌'}")
        if ble_stat['connected']:
            print(f"  蓝牙已连接")
    except:
        print(f"蓝牙状态: ❌")
    
    print("=" * 40)

def reset():
    """完全重置所有网络功能"""
    try:
        _wifi.active(False)
    except:
        pass
    try:
        _ap.active(False)
    except:
        pass
    try:
        if _ble:
            _ble.active(False)
    except:
        pass
    time.sleep(1)
    print("✅ 网络模块已重置")
    return True

# 导出函数
__all__ = [
    'wifi', 'ip', 'scan', 'disconnect', 'wifi_reset',
    'ap', 'ap_off', 'ap_clients',
    'ble', 'ble_off', 'ble_send', 'ble_receive', 'ble_scan', 'ble_connect', 'ble_status',
    'get_mac', 'status', 'reset'
]