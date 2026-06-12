"""
智能GPIO库 - 支持数字/模拟输出、RGB灯控制
适用于ESP32-S3，RGB灯在GPIO48
版本: 2.0
"""
from machine import Pin, ADC, PWM
import neopixel
import time

# ========== 配置区域 ==========
RGB_LED_PIN = 48  # 你的RGB灯在GPIO48
# =============================

# 缓存对象
_pin_cache = {}
_pwm_cache = {}
_neopixel_obj = None

# ESP32-S3 ADC引脚
AVAILABLE_ADC_PINS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

def pingwrite(pin, value, mode=None):
    """
    智能写入GPIO
    
    用法:
        # 数字输出
        pingwrite(2, 1)        # GPIO2输出高电平
        pingwrite(2, 0)        # GPIO2输出低电平
        
        # 模拟输出(PWM)
        pingwrite(2, 128)      # GPIO2输出50%占空比
        pingwrite(2, 255)      # GPIO2输出100%占空比
        
        # RGB灯控制 (自动使用GPIO48)
        pingwrite(36, [255,0,0])    # 红色
        pingwrite(36, [0,255,0])    # 绿色
        pingwrite(36, [0,0,255])    # 蓝色
        pingwrite(36, (255,255,0))  # 黄色（元组也可以）
        
        # 也可以直接写GPIO48
        pingwrite(48, [255,0,0])    # 红色
    """
    
    # ========== RGB灯控制 ==========
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return _rgb_write(pin, value)
    
    # ========== 数字/模拟输出 ==========
    # 自动判断输出类型
    if isinstance(value, bool) or value in [0, 1, "0", "1"]:
        return _digital_write(pin, value)
    elif isinstance(value, (int, float)) and 0 <= value <= 255:
        return _analog_write(pin, value)
    else:
        print(f"错误：无法识别的value值 {value}")
        return False

def _digital_write(pin, value):
    """数字输出"""
    # 转换值
    if value in [1, True, "1", "high", "HIGH"]:
        val = 1
    elif value in [0, False, "0", "low", "LOW"]:
        val = 0
    else:
        print(f"错误：无效的数字值 {value}")
        return False
    
    # 获取或创建Pin对象
    cache_key = f"out_{pin}"
    if cache_key not in _pin_cache:
        try:
            _pin_cache[cache_key] = Pin(pin, Pin.OUT)
        except Exception as e:
            print(f"初始化GPIO{pin}失败: {e}")
            return False
    
    _pin_cache[cache_key].value(val)
    print(f"✓ GPIO{pin} 数字输出: {val}")
    return True

def _analog_write(pin, value):
    """模拟输出（PWM）"""
    # 转换值到0-65535
    pwm_value = int(value * 65535 / 255)
    
    # 获取或创建PWM对象
    if pin not in _pwm_cache:
        try:
            _pwm_cache[pin] = PWM(Pin(pin), freq=1000, duty=0)
        except Exception as e:
            print(f"初始化PWM GPIO{pin}失败: {e}")
            return False
    
    _pwm_cache[pin].duty(pwm_value)
    print(f"✓ GPIO{pin} 模拟输出: {value}/255")
    return True

def _rgb_write(pin, color):
    """RGB灯控制 - 使用GPIO48"""
    global _neopixel_obj
    
    # 提示：无论写哪个引脚，都使用配置的RGB引脚
    if pin != RGB_LED_PIN:
        print(f"提示：RGB灯实际在GPIO{RGB_LED_PIN}，自动重定向")
    
    # 验证颜色格式
    if not isinstance(color, (list, tuple)) or len(color) != 3:
        print(f"错误：RGB颜色需要[R,G,B]格式")
        return False
    
    # 验证颜色值范围
    for c in color:
        if not (0 <= c <= 255):
            print(f"错误：颜色值需在0-255之间")
            return False
    
    # 初始化neopixel
    if _neopixel_obj is None:
        try:
            _pin = Pin(RGB_LED_PIN, Pin.OUT)
            _neopixel_obj = neopixel.NeoPixel(_pin, 1)
            print(f"✓ RGB灯初始化成功 (GPIO{RGB_LED_PIN})")
        except Exception as e:
            print(f"RGB灯初始化失败: {e}")
            return False
    
    # 设置颜色
    r, g, b = color[0], color[1], color[2]
    
    try:
        _neopixel_obj[0] = (r, g, b)
        _neopixel_obj.write()
        print(f"✓ RGB灯设置颜色: RGB({r},{g},{b})")
        return True
    except Exception as e:
        print(f"设置RGB颜色失败: {e}")
        return False

def pingread(pin, mode=None, pull=None):
    """
    智能读取GPIO
    
    用法:
        # 数字读取（默认）
        value = pingread(4)              # 普通读取
        value = pingread(4, pull="up")   # 上拉读取
        value = pingread(4, pull="down") # 下拉读取
        
        # 模拟读取(ADC)
        value = pingread(1, mode="analog")  # 读取ADC值 0-4095
    
    返回:
        数字模式: 0 或 1
        模拟模式: 0-4095
    """
    if mode == "analog":
        return _analog_read(pin)
    else:
        return _digital_read(pin, pull)

def _digital_read(pin, pull=None):
    """数字读取"""
    try:
        if pull == "up":
            p = Pin(pin, Pin.IN, Pin.PULL_UP)
        elif pull == "down":
            p = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        else:
            p = Pin(pin, Pin.IN)
        
        value = p.value()
        print(f"✓ GPIO{pin} 读取: {value}")
        return value
    except Exception as e:
        print(f"GPIO{pin}读取失败: {e}")
        return None

def _analog_read(pin):
    """模拟读取（ADC）"""
    if pin not in AVAILABLE_ADC_PINS:
        print(f"错误：GPIO{pin}不支持ADC")
        print(f"支持的ADC引脚: {AVAILABLE_ADC_PINS}")
        return None
    
    try:
        adc = ADC(Pin(pin))
        adc.atten(ADC.ATTN_11DB)  # 0-3.6V范围
        value = adc.read()  # 0-4095
        voltage = value * 3.3 / 4095
        print(f"✓ GPIO{pin} 模拟读取: {value}/4095 ({voltage:.2f}V)")
        return value
    except Exception as e:
        print(f"ADC读取失败: {e}")
        return None

# ========== 辅助函数 ==========
def rgb_off():
    """关闭RGB灯"""
    return pingwrite(RGB_LED_PIN, [0, 0, 0])

def rgb_set(r, g, b):
    """快速设置RGB颜色"""
    return pingwrite(RGB_LED_PIN, [r, g, b])

def pwm_stop(pin):
    """停止指定引脚的PWM输出"""
    if pin in _pwm_cache:
        _pwm_cache[pin].deinit()
        del _pwm_cache[pin]
        print(f"✓ GPIO{pin} PWM已停止")
        return True
    return False

def cleanup():
    """清理所有资源"""
    global _pin_cache, _pwm_cache, _neopixel_obj
    _pin_cache.clear()
    for pwm in _pwm_cache.values():
        pwm.deinit()
    _pwm_cache.clear()
    if _neopixel_obj:
        rgb_off()
        _neopixel_obj = None
    print("所有GPIO资源已清理")