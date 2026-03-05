#!/usr/bin/env python3
"""
Spatial Overlay: AQI 測站 + 避難所疊圖 (嚴格過濾版本)
使用更嚴格的邊界過濾移除海上避難所
"""

import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
import os
from datetime import datetime
import geopandas as gpd
from shapely.geometry import Point, Polygon

class SpatialOverlayStrict:
    def __init__(self):
        self.aqi_data = None
        self.shelter_data = None
        self.taiwan_center = [23.8, 120.9]
        
    def create_mock_aqi_data(self):
        """創建模擬AQI資料"""
        stations = [
            {"name": "台北", "county": "臺北市", "lat": 25.0173, "lon": 121.5395, "aqi": 45},
            {"name": "新北", "county": "新北市", "lat": 25.0167, "lon": 121.4667, "aqi": 52},
            {"name": "桃園", "county": "桃園市", "lat": 24.9936, "lon": 121.3010, "aqi": 38},
            {"name": "台中", "county": "臺中市", "lat": 24.1477, "lon": 120.6736, "aqi": 67},
            {"name": "台南", "county": "臺南市", "lat": 22.9999, "lon": 120.2269, "aqi": 41},
            {"name": "高雄", "county": "高雄市", "lat": 22.6273, "lon": 120.3014, "aqi": 150},
            {"name": "基隆", "county": "基隆市", "lat": 25.1276, "lon": 121.7392, "aqi": 35},
            {"name": "新竹", "county": "新竹市", "lat": 24.8138, "lon": 120.9675, "aqi": 42},
            {"name": "嘉義", "county": "嘉義市", "lat": 23.4801, "lon": 120.4491, "aqi": 48},
            {"name": "宜蘭", "county": "宜蘭縣", "lat": 24.6929, "lon": 121.7705, "aqi": 33},
            {"name": "花蓮", "county": "花蓮縣", "lat": 23.7519, "lon": 121.6067, "aqi": 28},
            {"name": "台東", "county": "臺東縣", "lat": 22.7583, "lon": 121.1528, "aqi": 25},
            {"name": "林口", "county": "新北市", "lat": 25.0777, "lon": 121.3163, "aqi": 120},
            {"name": "板橋", "county": "新北市", "lat": 25.0129, "lon": 121.4647, "aqi": 58},
            {"name": "三重", "county": "新北市", "lat": 25.0667, "lon": 121.4833, "aqi": 62}
        ]
        return pd.DataFrame(stations)
    
    def create_taiwan_boundary_strict(self):
        """創建更嚴格的台灣邊界多邊形"""
        # 更精確的台灣邊界坐標
        taiwan_coords = [
            [120.0, 25.3],   # 西北角
            [120.5, 25.5],   # 北端
            [121.0, 25.4],   # 東北
            [121.8, 25.0],   # 東北部
            [122.0, 24.5],   # 東北部
            [122.1, 24.0],   # 東部
            [122.0, 23.5],   # 東南部
            [121.9, 23.0],   # 東南
            [121.7, 22.5],   # 東南
            [121.5, 22.2],   # 東南
            [121.2, 22.0],   # 南端
            [120.8, 22.1],   # 西南
            [120.5, 22.3],   # 西南
            [120.2, 22.8],   # 西南
            [119.8, 23.2],   # 西部
            [119.5, 23.8],   # 西部
            [119.3, 24.2],   # 西北
            [119.5, 24.6],   # 西北
            [119.8, 25.0],   # 西北
            [120.0, 25.3],   # 回到起點
        ]
        
        # 創建多邊形
        taiwan_polygon = Polygon(taiwan_coords)
        
        # 創建GeoDataFrame
        gdf = gpd.GeoDataFrame(
            [{'name': 'Taiwan', 'geometry': taiwan_polygon}],
            crs='EPSG:4326'
        )
        
        return gdf
    
    def load_and_filter_shelters_strict(self):
        """載入並嚴格過濾避難所資料"""
        try:
            # 載入避難所資料
            df = pd.read_csv('data/shelters_cleaned.csv', encoding='utf-8-sig')
            print(f"原始避難所數量: {len(df)}")
            
            # 根據室內/室外欄位創建is_indoor欄位
            def classify_shelter(row):
                if pd.notna(row['室內']) and row['室內'] == '是':
                    return True
                elif pd.notna(row['室外']) and row['室外'] == '是':
                    return False
                else:
                    # 如果都沒有標記，根據名稱推斷
                    name = str(row['避難收容處所名稱']).lower()
                    indoor_keywords = ['活動中心', '禮堂', '體育館', '學校', '社區中心', '辦公處']
                    outdoor_keywords = ['公園', '廣場', '體育場', '停車場']
                    
                    for keyword in indoor_keywords:
                        if keyword in name:
                            return True
                    for keyword in outdoor_keywords:
                        if keyword in name:
                            return False
                    
                    # 預設為室內
                    return True
            
            df['is_indoor'] = df.apply(classify_shelter, axis=1)
            
            # 方法1: 簡單矩形過濾（最嚴格）
            df_filtered = df[
                (df['緯度'] > 21.5) &
                (df['緯度'] < 25.5) &
                (df['經度'] > 119.5) &
                (df['經度'] < 122.0)
            ]
            
            print(f"矩形過濾後避難所數量: {len(df_filtered)}")
            print(f"矩形過濾移除: {len(df) - len(df_filtered)} 個")
            
            # 方法2: GIS多邊形過濾
            try:
                # 創建避難所的GeoDataFrame
                geometry = [Point(lon, lat) for lon, lat in zip(df_filtered['經度'], df_filtered['緯度'])]
                shelters_gdf = gpd.GeoDataFrame(df_filtered, geometry=geometry, crs='EPSG:4326')
                
                # 創建台灣邊界
                taiwan_gdf = self.create_taiwan_boundary_strict()
                
                # 使用空間連接過濾出台灣內的避難所
                shelters_in_taiwan = gpd.sjoin(shelters_gdf, taiwan_gdf, predicate="within")
                
                print(f"GIS過濾後避難所數量: {len(shelters_in_taiwan)}")
                print(f"GIS過濾移除: {len(df_filtered) - len(shelters_in_taiwan)} 個")
                
                return shelters_in_taiwan
                
            except Exception as e:
                print(f"GIS過濾失敗: {e}")
                print("使用矩形過濾結果")
                return df_filtered
            
        except Exception as e:
            print(f"載入避難所資料失敗: {e}")
            return pd.DataFrame()
    
    def get_aqi_color(self, aqi):
        """根據AQI值獲取顏色"""
        if aqi <= 50:
            return 'green'
        elif aqi <= 100:
            return 'yellow'
        elif aqi <= 150:
            return 'orange'
        elif aqi <= 200:
            return 'red'
        elif aqi <= 300:
            return 'purple'
        else:
            return 'maroon'
    
    def get_aqi_level(self, aqi):
        """根據AQI值獲取等級描述"""
        if aqi <= 50:
            return '良好'
        elif aqi <= 100:
            return '普通'
        elif aqi <= 150:
            return '對敏感族群不健康'
        elif aqi <= 200:
            return '對所有族群不健康'
        elif aqi <= 300:
            return '非常不健康'
        else:
            return '危害'
    
    def create_map(self):
        """創建空間疊圖地圖"""
        print("正在創建嚴格過濾版Spatial Overlay地圖...")
        
        # 載入資料
        self.aqi_data = self.create_mock_aqi_data()
        self.shelter_data = self.load_and_filter_shelters_strict()
        
        print(f"AQI測站數量: {len(self.aqi_data)}")
        print(f"避難所數量: {len(self.shelter_data)}")
        
        # 創建基礎地圖
        m = folium.Map(
            location=self.taiwan_center,
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加AQI測站圖層（先創建但不添加到地圖）
        aqi_group = folium.FeatureGroup(name='AQI 測站')
        
        for _, station in self.aqi_data.iterrows():
            color = self.get_aqi_color(station['aqi'])
            level = self.get_aqi_level(station['aqi'])
            
            popup_content = f"""
            <b>{station['name']}</b><br>
            縣市: {station['county']}<br>
            AQI: {station['aqi']}<br>
            等級: {level}<br>
            <small>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}</small>
            """
            
            folium.CircleMarker(
                location=[station['lat'], station['lon']],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=2,
                fillColor=color,
                fillOpacity=0.8,
                tooltip=f"{station['name']}: AQI {station['aqi']}"
            ).add_to(aqi_group)
        
        # 添加避難所圖層
        indoor_group = folium.FeatureGroup(name='室內避難所')
        outdoor_group = folium.FeatureGroup(name='室外避難所')
        
        indoor_count = 0
        outdoor_count = 0
        
        for _, shelter in self.shelter_data.iterrows():
            try:
                # 獲取坐標（如果是GeoDataFrame，從geometry獲取）
                if hasattr(shelter, 'geometry'):
                    lat, lon = shelter.geometry.y, shelter.geometry.x
                else:
                    lat = float(shelter['緯度'])
                    lon = float(shelter['經度'])
                
                is_indoor = shelter['is_indoor']
                name = shelter['避難收容處所名稱']
                address = shelter.get('避難收容處所地址', '未知地址')
                capacity = shelter.get('預計收容人數', '未知')
                
                popup_content = f"""
                <b>{name}</b><br>
                地址: {address}<br>
                類型: {'室內' if is_indoor else '室外'}<br>
                收容人數: {capacity}<br>
                <small>坐標: ({lat:.6f}, {lon:.6f})</small>
                """
                
                if is_indoor:
                    icon = folium.Icon(color='blue', icon='home', prefix='fa')
                    indoor_count += 1
                    target_group = indoor_group
                else:
                    icon = folium.Icon(color='green', icon='tree', prefix='fa')
                    outdoor_count += 1
                    target_group = outdoor_group
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_content, max_width=300),
                    icon=icon,
                    tooltip=f"{name} ({'室內' if is_indoor else '室外'})"
                ).add_to(target_group)
                
            except Exception as e:
                continue
        
        # 先添加避難所圖層（底層）
        indoor_group.add_to(m)
        outdoor_group.add_to(m)
        
        # 再添加AQI熱力圖（中層）
        heat_data = []
        for _, station in self.aqi_data.iterrows():
            heat_data.append([station['lat'], station['lon'], float(station['aqi'])])
        
        if heat_data:
            heatmap_group = folium.FeatureGroup(name='AQI 熱力圖')
            HeatMap(
                heat_data,
                name='AQI 熱力圖',
                radius=15,
                blur=10,
                gradient={
                    0.0: 'green',
                    0.3: 'yellow',
                    0.5: 'orange',
                    0.7: 'red',
                    0.9: 'purple',
                    1.0: 'maroon'
                }
            ).add_to(heatmap_group)
            heatmap_group.add_to(m)
        
        # 最後添加AQI測站圖層（頂層，確保不被遮擋）
        aqi_group.add_to(m)
        
        # 添加圖例
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 220px; height: 340px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px">
        <h4>Spatial Overlay 圖例 (嚴格過濾)</h4>
        <b>AQI 測站</b><br>
        <i class="fa fa-circle" style="color:green"></i> 良好 (0-50)<br>
        <i class="fa fa-circle" style="color:yellow"></i> 普通 (51-100)<br>
        <i class="fa fa-circle" style="color:orange"></i> 對敏感族群不健康 (101-150)<br>
        <i class="fa fa-circle" style="color:red"></i> 對所有族群不健康 (151-200)<br>
        <i class="fa fa-circle" style="color:purple"></i> 非常不健康 (201-300)<br>
        <i class="fa fa-circle" style="color:maroon"></i> 危害 (301+)<br><br>
        <b>避難所</b><br>
        <i class="fa fa-home" style="color:blue"></i> 室內避難所<br>
        <i class="fa fa-tree" style="color:green"></i> 室外避難所<br><br>
        <b>過濾方式</b><br>
        📐 矩形邊界: 21.5-25.5°N, 119.5-122.0°E<br>
        🗺️ GIS多邊形: 台灣精確邊界<br>
        🚫 移除海上避難所<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 添加圖層控制
        folium.LayerControl().add_to(m)
        
        # 添加全屏功能
        from folium.plugins import Fullscreen
        Fullscreen().add_to(m)
        
        # 儲存地圖
        output_file = 'outputs/spatial_overlay_strict.html'
        m.save(output_file)
        
        print(f"地圖已儲存至: {output_file}")
        print(f"統計: 室內避難所 {indoor_count} 個, 室外避難所 {outdoor_count} 個")
        
        return output_file, indoor_count, outdoor_count

def main():
    """主程式"""
    print("=== Spatial Overlay: AQI 測站 + 避難所疊圖 (嚴格過濾版本) ===")
    
    # 確保輸出目錄存在
    os.makedirs('outputs', exist_ok=True)
    
    # 創建地圖
    map_creator = SpatialOverlayStrict()
    output_file, indoor_count, outdoor_count = map_creator.create_map()
    
    print(f"\n嚴格過濾版Spatial Overlay地圖創建完成！")
    print(f"檔案位置: {output_file}")
    print(f"室內避難所: {indoor_count} 個")
    print(f"室外避難所: {outdoor_count} 個")
    print(f"請用瀏覽器開啟查看完整的地圖和互動功能")
    print(f"此版本使用嚴格的邊界過濾，應該完全移除海上避難所")

if __name__ == "__main__":
    main()
