#!/usr/bin/env python3
"""
避難收容處所空間審計程式
檢查坐標品質：CRS混淆、離群值偵測
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.font_manager import FontProperties
import warnings
warnings.filterwarnings('ignore')

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class ShelterSpatialAudit:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file, encoding='utf-8')
        self.taiwan_bounds = {
            'lat_min': 21.5,  # 台灣最南端
            'lat_max': 25.5,  # 台灣最北端
            'lon_min': 119.5, # 台灣最西端
            'lon_max': 122.5  # 台灣最東端
        }
        
    def analyze_coordinate_format(self):
        """分析坐標格式 - 判斷是經緯度還是二度分帶"""
        print("=== 坐標格式分析 ===")
        
        # 提取經緯度欄位
        lons = self.df['經度'].dropna()
        lats = self.df['緯度'].dropna()
        
        print(f"總記錄數: {len(self.df)}")
        print(f"有效坐標數: {len(lons)}")
        
        # 判斷坐標系統
        # 經緯度範圍檢查
        lat_in_range = ((lats >= self.taiwan_bounds['lat_min']) & 
                       (lats <= self.taiwan_bounds['lat_max'])).sum()
        lon_in_range = ((lons >= self.taiwan_bounds['lon_min']) & 
                       (lons <= self.taiwan_bounds['lon_max'])).sum()
        
        # 二度分帶範圍檢查 (TWD97 TM2: 東經 170000-350000, 北緯 2400000-2800000)
        tm2_lon_range = ((lons >= 170000) & (lons <= 350000)).sum()
        tm2_lat_range = ((lats >= 2400000) & (lats <= 2800000)).sum()
        
        print(f"\n坐標範圍分析:")
        print(f"經緯度範圍內的點: 緯度 {lat_in_range}, 經度 {lon_in_range}")
        print(f"二度分帶範圍內的點: 緯度 {tm2_lat_range}, 經度 {tm2_lon_range}")
        
        # 判斷坐標系統
        if lat_in_range > len(lats) * 0.8 and lon_in_range > len(lons) * 0.8:
            coordinate_system = "WGS84 (經緯度 EPSG:4326)"
            print(f"\n判斷結果: {coordinate_system}")
        elif tm2_lat_range > len(lats) * 0.8 and tm2_lon_range > len(lons) * 0.8:
            coordinate_system = "TWD97 TM2 (二度分帶 EPSG:3826)"
            print(f"\n判斷結果: {coordinate_system}")
        else:
            coordinate_system = "混合或未知坐標系統"
            print(f"\n判斷結果: {coordinate_system}")
            
        return coordinate_system
    
    def detect_outliers(self):
        """偵測離群值"""
        print("\n=== 離群值偵測 ===")
        
        # 移除缺失值
        valid_coords = self.df[['經度', '緯度']].dropna()
        
        # 檢查 (0,0) 坐標
        zero_coords = valid_coords[(valid_coords['經度'] == 0) & (valid_coords['緯度'] == 0)]
        print(f"(0,0) 坐標數量: {len(zero_coords)}")
        
        # 檢查台灣邊界外的坐標
        outside_taiwan = valid_coords[
            (valid_coords['緯度'] < self.taiwan_bounds['lat_min']) | 
            (valid_coords['緯度'] > self.taiwan_bounds['lat_max']) |
            (valid_coords['經度'] < self.taiwan_bounds['lon_min']) | 
            (valid_coords['經度'] > self.taiwan_bounds['lon_max'])
        ]
        print(f"台灣邊界外的坐標數量: {len(outside_taiwan)}")
        
        # 檢查極端值
        extreme_lat = valid_coords[
            (valid_coords['緯度'] < -90) | (valid_coords['緯度'] > 90)
        ]
        extreme_lon = valid_coords[
            (valid_coords['經度'] < -180) | (valid_coords['經度'] > 180)
        ]
        print(f"極端緯度值數量: {len(extreme_lat)}")
        print(f"極端經度值數量: {len(extreme_lon)}")
        
        # 統計摘要
        print(f"\n坐標統計摘要:")
        print(f"緯度 - 最小值: {valid_coords['緯度'].min():.6f}, 最大值: {valid_coords['緯度'].max():.6f}")
        print(f"經度 - 最小值: {valid_coords['經度'].min():.6f}, 最大值: {valid_coords['經度'].max():.6f}")
        
        return {
            'zero_coords': len(zero_coords),
            'outside_taiwan': len(outside_taiwan),
            'extreme_lat': len(extreme_lat),
            'extreme_lon': len(extreme_lon),
            'valid_coords': len(valid_coords)
        }
    
    def plot_coordinate_distribution(self):
        """繪製坐標分佈圖"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 移除缺失值
        valid_coords = self.df[['經度', '緯度']].dropna()
        
        # 1. 經度分佈
        axes[0, 0].hist(valid_coords['經度'], bins=50, alpha=0.7, color='blue', edgecolor='black')
        axes[0, 0].set_title('經度分佈')
        axes[0, 0].set_xlabel('經度')
        axes[0, 0].set_ylabel('頻率')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 緯度分佈
        axes[0, 1].hist(valid_coords['緯度'], bins=50, alpha=0.7, color='red', edgecolor='black')
        axes[0, 1].set_title('緯度分佈')
        axes[0, 1].set_xlabel('緯度')
        axes[0, 1].set_ylabel('頻率')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 散點圖
        axes[1, 0].scatter(valid_coords['經度'], valid_coords['緯度'], alpha=0.6, s=10)
        axes[1, 0].set_title('坐標散點圖')
        axes[1, 0].set_xlabel('經度')
        axes[1, 0].set_ylabel('緯度')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 添加台灣邊界框
        axes[1, 0].axvspan(self.taiwan_bounds['lon_min'], self.taiwan_bounds['lon_max'], 
                          self.taiwan_bounds['lat_min'], self.taiwan_bounds['lat_max'], 
                          alpha=0.2, color='green', label='台灣邊界')
        axes[1, 0].legend()
        
        # 4. 箱型圖
        coord_data = [valid_coords['經度'], valid_coords['緯度']]
        axes[1, 1].boxplot(coord_data, labels=['經度', '緯度'])
        axes[1, 1].set_title('坐標箱型圖')
        axes[1, 1].set_ylabel('坐標值')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('outputs/coordinate_distribution_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("坐標分佈圖已儲存至 outputs/coordinate_distribution_analysis.png")
    
    def generate_audit_report(self):
        """生成審計報告"""
        print("\n" + "="*50)
        print("避難收容處所空間審計報告")
        print("="*50)
        
        # 基本統計
        total_records = len(self.df)
        valid_coords = self.df[['經度', '緯度']].dropna()
        missing_coords = total_records - len(valid_coords)
        
        print(f"\n基本統計:")
        print(f"  總記錄數: {total_records}")
        print(f"  有效坐標數: {len(valid_coords)}")
        print(f"  缺失坐標數: {missing_coords}")
        print(f"  坐標完整率: {len(valid_coords)/total_records*100:.2f}%")
        
        # 坐標系統分析
        coord_system = self.analyze_coordinate_format()
        
        # 離群值分析
        outliers = self.detect_outliers()
        
        # 縣市分佈
        print(f"\n縣市分佈:")
        city_count = self.df['縣市及鄉鎮市區'].str.extract(r'([^縣市]+)')[0].value_counts().head(10)
        for city, count in city_count.items():
            print(f"  {city}: {count} 處")
        
        # 災害類型分析
        print(f"\n適用災害類型:")
        disaster_types = self.df['適用災害類別'].dropna()
        all_disasters = []
        for disasters in disaster_types:
            if pd.notna(disasters):
                all_disasters.extend([d.strip() for d in disasters.split(',')])
        
        disaster_count = pd.Series(all_disasters).value_counts()
        for disaster, count in disaster_count.items():
            print(f"  {disaster}: {count} 處")
        
        return {
            'total_records': total_records,
            'valid_coords': len(valid_coords),
            'coordinate_system': coord_system,
            'outliers': outliers
        }
    
    def export_cleaned_data(self):
        """匯出清理後的資料"""
        # 移除明顯的錯誤坐標
        valid_coords = self.df[['經度', '緯度']].dropna()
        
        # 過濾條件
        filtered_df = self.df[
            (self.df['經度'].notna()) & 
            (self.df['緯度'].notna()) &
            (self.df['經度'] != 0) & 
            (self.df['緯度'] != 0) &
            (self.df['經度'] >= self.taiwan_bounds['lon_min']) & 
            (self.df['經度'] <= self.taiwan_bounds['lon_max']) &
            (self.df['緯度'] >= self.taiwan_bounds['lat_min']) & 
            (self.df['緯度'] <= self.taiwan_bounds['lat_max'])
        ]
        
        # 儲存清理後的資料
        filtered_df.to_csv('data/shelter_locations_cleaned.csv', index=False, encoding='utf-8-sig')
        
        print(f"\n資料匯出:")
        print(f"  原始資料: {len(self.df)} 筆")
        print(f"  清理後資料: {len(filtered_df)} 筆")
        print(f"  移除記錄: {len(self.df) - len(filtered_df)} 筆")
        print(f"  清理後資料已儲存至: data/shelter_locations_cleaned.csv")
        
        return filtered_df

def main():
    """主程式"""
    print("開始進行避難收容處所空間審計...")
    
    # 確保輸出目錄存在
    import os
    os.makedirs('outputs', exist_ok=True)
    
    # 初始化審計器
    auditor = ShelterSpatialAudit('data/shelter_locations.csv')
    
    # 生成審計報告
    report = auditor.generate_audit_report()
    
    # 繪製坐標分佈圖
    auditor.plot_coordinate_distribution()
    
    # 匯出清理後的資料
    cleaned_data = auditor.export_cleaned_data()
    
    print(f"\n空間審計完成！")
    print(f"坐標系統: {report['coordinate_system']}")
    print(f"有效坐標: {report['valid_coords']}/{report['total_records']}")
    print(f"離群值: {sum(report['outliers'].values())} 個")

if __name__ == "__main__":
    main()
