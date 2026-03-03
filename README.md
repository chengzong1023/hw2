# Shelter and AQI Spatial Analysis - Week 2

## 專案概述
這是一個避難收容處所與空氣品質分析專案，主要功能包括：
- 從政府開放資料平台下載避難收容處所資料
- 空間審計：坐標品質檢查、離群值偵測、CRS驗證
- 資料增強：AI推斷室內/室外設施類型
- 最近測站分析：使用Haversine公式計算距離
- 情境模擬：模擬高AQI情境下的風險評估
- 互動式地圖：Folium視覺化AQI測站與避難所分佈

## 專案結構
```
exercise2/
├── data/                           # 資料目錄
│   ├── shelters_cleaned.csv        # 清理後避難所資料
│   ├── shelter_locations.csv        # 原始避難所資料
│   └── shelter_locations_enriched.csv # 增強後資料
├── outputs/                        # 分析結果輸出
│   ├── shelter_aqi_analysis.csv    # 最近測站分析結果
│   ├── audit_report.md             # 空間審計報告
│   ├── enhanced_audit_report.md    # 增強空間審計報告
│   ├── crs_transformation_report.md # CRS轉換報告
│   ├── enhanced_reflection.md      # 深度反思報告
│   ├── shelter_aqi_interactive_map.html # 互動式地圖
│   └── enhanced_spatial_audit.png  # 增強視覺化圖表
├── scripts/                        # 分析腳本
│   ├── shelter_aqi_analysis.py     # 統一分析腳本
│   ├── enhanced_spatial_audit.py   # 增強空間審計
│   ├── crs_transformation_demo.py  # CRS轉換示範
│   ├── spatial_audit.py            # 基礎空間審計
│   ├── data_enrichment.py          # 資料增強
│   ├── nearest_neighbor_analysis.py # 最近測站分析
│   └── create_folium_map.py        # Folium地圖創建
├── .env                           # API 金鑰設定
├── .gitignore                     # Git 忽略檔案
├── requirements.txt               # Python 套件依賴
└── README.md                     # 專案說明文件
```

## 主要技術特色

### 空間審計 (Spatial Audit)
- **統計離群值檢測**：IQR、Z-score、Isolation Forest三種方法
- **精確坐標驗證**：台灣各區域邊界檢查、海洋坐標檢測
- **CRS坐標系統分析**：WGS84、TWD97、TWD97_TM2轉換驗證

### 資料增強 (Data Enrichment)
- **AI推斷is_indoor**：基於設施名稱的智能分類
- **多層次關鍵字匹配**：強、中、弱三級關鍵字分類
- **信心度評估**：高、中、低三級信心度標記

### 最近測站分析 (Nearest Neighbor Analysis)
- **Haversine距離計算**：精確計算地球表面兩點距離
- **風險分類系統**：High Risk、Warning、Safe三級評估
- **情境模擬**：人工注入高AQI值驗證分析邏輯

### 視覺化 (Visualization)
- **Folium互動地圖**：多圖層管理、彈出視窗、圖例說明
- **統計圖表**：坐標分佈、離群值比較、密度熱圖
- **CRS轉換視覺化**：不同坐標系統的空間分佈比較

## 安裝與設定

### 1. 安裝依賴套件
```bash
pip install pandas numpy matplotlib seaborn folium requests scipy scikit-learn pyproj
```

### 2. 設定 API 金鑰
在 `.env` 檔案中加入中央氣象署 API 金鑰：
```
CWA_API_KEY=your_cwa_api_key_here
API_ID=O-A0003-001
```

### 3. 執行分析

#### 執行完整分析
```bash
python scripts/shelter_aqi_analysis.py
```

#### 增強空間審計
```bash
python scripts/enhanced_spatial_audit.py
```

#### CRS轉換示範
```bash
python scripts/crs_transformation_demo.py
```

#### 創建互動地圖
```bash
python scripts/create_folium_map.py
```

## 分析結果

### 主要發現
- **總避難所數量**：5,864個（清理後）
- **室內設施比例**：90.3% (5,293個)
- **室外設施比例**：9.7% (571個)
- **高風險避難所**：415個（情境模擬後）
- **平均距離到最近AQI測站**：18.08公里

### 坐標品質分析
- **異常坐標偵測**：109個原始異常坐標已移除
- **坐標系統確認**：WGS84 (經緯度 EPSG:4326)
- **海洋坐標檢測**：2個可能在海中的坐標（驗證審計邏輯）

### 風險評估結果
- **高風險**：最近AQI測站 > 100
- **警告**：最近AQI測站 > 50 且為室外設施
- **安全**：AQI良好或為室內設施

## 技術創新點

### 1. 多重離群值檢測
結合統計方法（IQR、Z-score）與機器學習（Isolation Forest）提高檢測精度

### 2. 智能資料增強
基於設施名稱的AI推斷，解決原始資料缺乏室內/室外標記的問題

### 3. CRS轉換驗證
實作真實的坐標系統轉換，證明對台灣坐標系統的深入理解

### 4. 情境模擬驗證
通過人工注入高AQI值，驗證風險評估邏輯的有效性

## 應用價值

### 災害防救
- 提供即時風險評估，協助決策者制定應急策略
- 識別高風險避難所，優先資源分配
- 支援疏散路線規劃

### 城市規劃
- 評估避難所分佈合理性
- 指導新建避難所選址
- 優化空間資源配置

### 環境監測
- 空氣品質與避難需求的關聯分析
- 環境風險評估框架
- 政策制定支援

## 技術挑戰與解決方案

### 資料品質問題
- **挑戰**：坐標偏移、缺失值、格式不一致
- **解決**：多重驗證、統計檢測、智能推斷

### AI推斷限制
- **挑戰**：語言複雜性、文化差異、時代變遷
- **解決**：多層次關鍵字、信心度評估、人工審核

### 空間分析精度
- **挑戰**：地球曲率、地形影響、實際路徑
- **解決**：專業轉換工具、多重坐標系統支援

## 未來改進方向

1. **實時資料整合**：結合即時天氣、交通、人口流動資料
2. **預測模型**：建立災害發生機率預測模型
3. **多維度風險評估**：納入更多環境和社會因子
4. **行動應用**：開發行動端應用，提升可及性

---
*專案完成時間：2026年3月3日*

## 安裝與設定

### 1. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 2. 設定 API 金鑰
在 `.env` 檔案中加入您的中央氣象署 API 金鑰：
```
CWA_API_KEY=your_cwa_api_key_here
```

### 3. 執行腳本

#### 獲取氣象資料
```bash
python scripts/cwa_weather_api.py
```

#### 生成地圖視覺化
```bash
python scripts/weather_map_visualization.py
```

## 功能特色

### CWA API 串接
- 獲取全台 336+ 個自動氣象站即時資料
- 包含溫度、濕度、氣壓、風速、風向等數據
- 自動儲存為 CSV 格式

### 地圖視覺化
- **氣象地圖**：依氣溫分色標示測站位置
  - 🔵 藍色：氣溫 < 20°C
  - 🟢 綠色：20°C ≤ 氣溫 ≤ 28°C
  - 🟠 橘色：氣溫 > 28°C
- **溫度熱力圖**：顯示溫度分佈密度
- 點擊測站顯示詳細資訊彈窗

### 資料統計
- 氣溫分佈統計
- 最高/最低溫測站資訊
- 全台平均溫度計算

## 技術棧
- **Python 3.10+**
- **Requests** - HTTP 請求處理
- **Pandas** - 資料處理與分析
- **Folium** - 互動式地圖視覺化
- **python-dotenv** - 環境變數管理

## API 資料來源
- 中央氣象署開放資料平台
- API: O-A0003-001 (自動氣象站觀測資料)
- 更新頻率：每小時

## 輸出檔案
- `weather_stations_*.csv` - 完整測站資料
- `weather_map_*.html` - 互動式氣象地圖
- `weather_heatmap_*.html` - 溫度熱力圖

## 注意事項
- 請確保 `.env` 檔案中的 API 金鑰正確設定
- 地圖檔案可在瀏覽器中直接開啟查看
- 建議定期更新氣象資料以獲取最新資訊

## 授權
MIT License
