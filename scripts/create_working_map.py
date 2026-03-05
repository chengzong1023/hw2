#!/usr/bin/env python3
"""
創建真正能工作的Folium地圖
"""

import pandas as pd
import folium
import os

def create_working_map():
    """創建簡單但有效的地圖"""
    
    # 台灣中心坐標
    taiwan_center = [23.8, 120.9]
    
    # 創建基礎地圖
    m = folium.Map(
        location=taiwan_center,
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # 添加一些AQI測站
    aqi_stations = [
        {"name": "台北", "lat": 25.0173, "lon": 121.5395, "aqi": 45},
        {"name": "新北", "lat": 25.0167, "lon": 121.4667, "aqi": 52},
        {"name": "台中", "lat": 24.1477, "lon": 120.6736, "aqi": 67},
        {"name": "高雄", "lat": 22.6273, "lon": 120.3014, "aqi": 150},
        {"name": "台南", "lat": 22.9999, "lon": 120.2269, "aqi": 41},
    ]
    
    # 添加AQI測站標記
    for station in aqi_stations:
        # 根據AQI值決定顏色
        if station["aqi"] <= 50:
            color = 'green'
        elif station["aqi"] <= 100:
            color = 'yellow'
        elif station["aqi"] <= 150:
            color = 'orange'
        else:
            color = 'red'
        
        folium.CircleMarker(
            location=[station["lat"], station["lon"]],
            radius=10,
            popup=f"{station['name']}<br>AQI: {station['aqi']}",
            color='black',
            weight=2,
            fillColor=color,
            fillOpacity=0.8
        ).add_to(m)
    
    # 添加一些避難所
    shelters = [
        {"name": "台北活動中心", "lat": 25.0200, "lon": 121.5400, "indoor": True},
        {"name": "新北公園", "lat": 25.0100, "lon": 121.4600, "indoor": False},
        {"name": "台中體育館", "lat": 24.1500, "lon": 120.6800, "indoor": True},
        {"name": "高雄廣場", "lat": 22.6200, "lon": 120.3100, "indoor": False},
    ]
    
    # 添加避難所標記
    for shelter in shelters:
        if shelter["indoor"]:
            icon = folium.Icon(color='blue', icon='home', prefix='fa')
        else:
            icon = folium.Icon(color='green', icon='tree', prefix='fa')
        
        folium.Marker(
            location=[shelter["lat"], shelter["lon"]],
            popup=f"{shelter['name']}<br>類型: {'室內' if shelter['indoor'] else '室外'}",
            icon=icon
        ).add_to(m)
    
    # 添加圖例
    legend_html = '''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 200px; height: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>圖例</h4>
    <b>AQI測站</b><br>
    <i class="fa fa-circle" style="color:green"></i> 良好 (0-50)<br>
    <i class="fa fa-circle" style="color:yellow"></i> 普通 (51-100)<br>
    <i class="fa fa-circle" style="color:orange"></i> 不健康 (101-150)<br>
    <i class="fa fa-circle" style="color:red"></i> 危害 (151+)<br><br>
    <b>避難所</b><br>
    <i class="fa fa-home" style="color:blue"></i> 室內避難所<br>
    <i class="fa fa-tree" style="color:green"></i> 室外避難所<br>
    </div>
    '''
    
    # 添加圖例到地圖
    from folium import Element
    m.get_root().html.add_child(Element(legend_html))
    
    # 儲存地圖
    output_file = 'outputs/working_map.html'
    m.save(output_file)
    
    print(f"地圖已創建: {output_file}")
    print("請用瀏覽器開啟此檔案查看地圖")
    
    return output_file

if __name__ == "__main__":
    # 確保輸出目錄存在
    os.makedirs('outputs', exist_ok=True)
    
    # 創建地圖
    create_working_map()
