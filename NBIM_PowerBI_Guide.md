# NBIM Investment Portfolio Dashboard - Power BI Implementation Guide

## Overview

This guide walks you through recreating the **Norges Bank Investment Management (NBIM) "All Investments"** visualization in Power BI. The NBIM dashboard features:

- An interactive **treemap** showing investments sized by value, colored by share of fund
- **Filters** for year, asset class (Equities, Fixed Income, Real Estate, Infrastructure), country, and sector
- **KPI cards** showing total fund value, number of companies, annual return
- **Top holdings table** with company details
- **Country and sector breakdowns**

---

## 1. Data Model

### 1.1 Required Tables

Create or import the following tables:

#### **Investments (Fact Table)**
| Column | Type | Description |
|--------|------|-------------|
| InvestmentID | Text | Unique identifier |
| CompanyName | Text | Company name (e.g., "NVIDIA Corp") |
| Year | Integer | Reporting year (1998-2025) |
| AssetClass | Text | Equities / Fixed Income / Real Estate / Infrastructure |
| Country | Text | Country of investment |
| Sector | Text | Industry sector |
| ValueNOK | Decimal | Investment value in NOK billions |
| ShareOfFund | Decimal | Percentage share of total fund |
| Currency | Text | Original currency |

#### **Countries (Dimension Table)**
| Column | Type |
|--------|------|
| CountryCode | Text |
| CountryName | Text |
| Region | Text |
| Continent | Text |

#### **Sectors (Dimension Table)**
| Column | Type |
|--------|------|
| SectorID | Text |
| SectorName | Text |
| SectorGroup | Text |

#### **AssetClasses (Dimension Table)**
| Column | Type |
|--------|------|
| AssetClassID | Integer |
| AssetClassName | Text |
| TargetAllocation | Decimal |

### 1.2 Sample Data

You can source real data from NBIM's public holdings disclosures at:
- https://www.nbim.no/en/investments/all-investments/ (download available as CSV/Excel)
- Annual reports with full holdings lists

### 1.3 Relationships

```
Countries.CountryCode  -->  Investments.Country  (1:Many)
Sectors.SectorID       -->  Investments.Sector   (1:Many)
AssetClasses.AssetClassID --> Investments.AssetClass (1:Many)
```

---

## 2. DAX Measures

Create these measures in Power BI:

```dax
// Total Fund Value
Total Fund Value =
SUM(Investments[ValueNOK])

// Number of Companies
Company Count =
DISTINCTCOUNT(Investments[CompanyName])

// Number of Countries
Country Count =
DISTINCTCOUNT(Investments[Country])

// Average Share of Fund
Avg Share of Fund =
AVERAGE(Investments[ShareOfFund])

// Year-over-Year Return (if return data available)
YoY Return =
VAR CurrentYear = MAX(Investments[Year])
VAR CurrentValue = CALCULATE(SUM(Investments[ValueNOK]), Investments[Year] = CurrentYear)
VAR PriorValue = CALCULATE(SUM(Investments[ValueNOK]), Investments[Year] = CurrentYear - 1)
RETURN
DIVIDE(CurrentValue - PriorValue, PriorValue, 0)

// Top N Holdings Rank
Holding Rank =
RANKX(
    ALL(Investments[CompanyName]),
    [Total Fund Value],,
    DESC,
    DENSE
)

// Share of Fund % (for color coding)
Share Pct =
DIVIDE(
    SUM(Investments[ValueNOK]),
    CALCULATE(SUM(Investments[ValueNOK]), ALL(Investments)),
    0
)
```

---

## 3. Dashboard Layout (Page 1: Main Dashboard)

### 3.1 Page Setup
- **Canvas size**: 1920 x 1080 (16:9)
- **Background**: Dark theme (#1a1a2e or #0d1117) to match NBIM's dark aesthetic
- **Font**: Segoe UI or similar clean sans-serif

### 3.2 Component Layout

```
+------------------------------------------------------------------+
|  [Logo]   ALL INVESTMENTS    [Year Slicer] [Asset Class Buttons]  |
+------------------------------------------------------------------+
|                                                                    |
|  [Total Value]  [Companies]  [Annual Return]  [Countries]         |
|   KPI Card       KPI Card     KPI Card         KPI Card           |
|                                                                    |
+------------------------------------------------------------------+
|                                          |                         |
|                                          |  [Country Slicer]       |
|        TREEMAP VISUALIZATION             |  [Sector Slicer]        |
|        (Investments by Company)          |  [Search Box]           |
|        Size = Value                      |                         |
|        Color = Share of Fund             |                         |
|                                          |                         |
+------------------------------------------+-------------------------+
|                                          |                         |
|  [Top 15 Holdings Table]                 |  [Sector Donut Chart]   |
|  Company | Value | Sector | Country      |                         |
|                                          |  [Country Bar Chart]    |
|                                          |                         |
+------------------------------------------+-------------------------+
```

---

## 4. Building Each Visual

### 4.1 Treemap (Main Visual)

This is the centerpiece, replicating NBIM's interactive investment map.

1. **Insert** > **Treemap** visualization
2. **Configuration**:
   - **Group**: `Investments[Sector]` (Level 1), `Investments[CompanyName]` (Level 2)
   - **Values**: `[Total Fund Value]`
3. **Conditional Formatting** (for color):
   - Click on the treemap > Format > Data colors > Advanced controls
   - Use **Gradient** color scale:
     - **Minimum**: Light blue (#b3d9ff) = Lowest share
     - **Maximum**: Dark blue (#003366) = Highest share
   - **Based on**: `[Share Pct]` measure
4. **Tooltips**: Add `CompanyName`, `ValueNOK`, `Country`, `Sector`, `ShareOfFund`
5. **Interactions**: Enable cross-filtering with other visuals

### 4.2 KPI Cards

For each KPI, add a **Card** visual:

| KPI | Value | Format |
|-----|-------|--------|
| Total Fund Value | `[Total Fund Value]` | "0.0 bn NOK" |
| Companies | `[Company Count]` | "#,##0" |
| Annual Return | `[YoY Return]` | "0.0%" |
| Countries | `[Country Count]` | "#,##0" |

**Styling**:
- Background: Transparent or semi-transparent dark
- Font color: White (#FFFFFF)
- Value font size: 28-32pt
- Label font size: 10-12pt

### 4.3 Year Slicer

1. **Insert** > **Slicer**
2. **Field**: `Investments[Year]`
3. **Style**: Dropdown or horizontal list
4. **Default**: Latest year (2025)

### 4.4 Asset Class Filter Buttons

1. **Insert** > **Slicer**
2. **Field**: `Investments[AssetClass]`
3. **Style**: Tile / Horizontal buttons
4. **Selection**: Single-select or multi-select

### 4.5 Top Holdings Table

1. **Insert** > **Table** visualization
2. **Columns**:
   - Rank: `[Holding Rank]`
   - Company: `Investments[CompanyName]`
   - Value: `[Total Fund Value]`
   - Sector: `Investments[Sector]`
   - Country: `Investments[Country]`
3. **Filter**: Top N filter on `[Holding Rank]` <= 15
4. **Conditional formatting**: Data bars on the Value column

### 4.6 Sector Donut Chart

1. **Insert** > **Donut Chart**
2. **Legend**: `Investments[Sector]`
3. **Values**: `[Total Fund Value]`
4. **Colors**: Use a professional palette matching NBIM's brand

### 4.7 Country Bar Chart

1. **Insert** > **Stacked Bar Chart**
2. **Axis**: `Investments[Country]`
3. **Values**: `[Total Fund Value]`
4. **Sort**: Descending by value
5. **Top N**: Show top 20 countries

### 4.8 Country/Sector Slicers (Side Panel)

1. **Country Slicer**: Dropdown with search enabled
2. **Sector Slicer**: Dropdown with search enabled
3. **Search Box**: Use a text slicer or add a search visual from AppSource

---

## 5. Theming & Styling

### 5.1 Custom Theme JSON

Save as `nbim-theme.json` and import via View > Themes > Browse for themes:

```json
{
  "name": "NBIM Investment Theme",
  "dataColors": [
    "#003366", "#0066cc", "#3399ff", "#66b2ff", "#99ccff",
    "#b3d9ff", "#1a5276", "#2e86c1", "#5dade2", "#85c1e9"
  ],
  "background": "#0d1117",
  "foreground": "#ffffff",
  "tableAccent": "#0066cc",
  "visualStyles": {
    "*": {
      "*": {
        "background": [{ "color": { "solid": { "color": "#161b22" } } }],
        "outlineColor": [{ "color": { "solid": { "color": "#30363d" } } }],
        "foreground": [{ "color": { "solid": { "color": "#e6edf3" } } }]
      }
    }
  }
}
```

### 5.2 Color Palette

| Purpose | Color | Hex |
|---------|-------|-----|
| Background | Dark navy | #0d1117 |
| Card background | Dark gray | #161b22 |
| Primary accent | NBIM Blue | #003366 |
| Secondary accent | Light blue | #3399ff |
| Text primary | White | #e6edf3 |
| Text secondary | Gray | #8b949e |
| Highest share | Deep blue | #003366 |
| Lowest share | Light blue | #b3d9ff |
| Positive return | Green | #2ea043 |
| Negative return | Red | #f85149 |

---

## 6. Interactivity

### 6.1 Cross-Filtering
- Enable cross-filtering between treemap, table, donut chart, and bar chart
- Clicking a sector in the treemap filters all other visuals
- Clicking a country in the bar chart highlights that country's investments

### 6.2 Drill-Through Pages

Create a **Company Detail** drill-through page:
1. Right-click a company in the treemap or table > Drill through
2. Detail page shows:
   - Company name and logo
   - Historical investment value (line chart by year)
   - Sector and country info
   - Share of fund over time

### 6.3 Bookmarks for Asset Class Views
Create bookmarks for quick switching:
- **All Investments** (default)
- **Equities Only**
- **Fixed Income Only**
- **Real Estate Only**
- **Infrastructure Only**

### 6.4 Tooltips
Add a custom tooltip page with:
- Company name
- Investment value
- Percentage of fund
- Small sparkline of value over time

---

## 7. Advanced Features

### 7.1 Treemap with Custom Visual

For a more NBIM-like treemap experience, consider:
- **Charticulator** (custom visual builder in Power BI)
- **Deneb** (Vega/Vega-Lite custom visuals) for more control over the treemap layout

Example Deneb/Vega-Lite spec for a custom treemap:

```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "data": {"name": "dataset"},
  "mark": {"type": "rect", "stroke": "#0d1117", "strokeWidth": 1},
  "encoding": {
    "x": {"field": "CompanyName", "type": "nominal"},
    "y": {"field": "ValueNOK", "type": "quantitative"},
    "color": {
      "field": "ShareOfFund",
      "type": "quantitative",
      "scale": {"scheme": "blues"}
    },
    "size": {"field": "ValueNOK", "type": "quantitative"},
    "tooltip": [
      {"field": "CompanyName"},
      {"field": "ValueNOK", "format": ",.0f"},
      {"field": "Sector"},
      {"field": "Country"}
    ]
  }
}
```

### 7.2 World Map Visual

Add a **Map** visual showing investment distribution:
1. **Insert** > **Map** or **Filled Map**
2. **Location**: `Countries[CountryName]`
3. **Size**: `[Total Fund Value]`
4. **Color saturation**: `[Share Pct]`

### 7.3 Time Animation

Add a **Play Axis** (timeline slicer) to animate investments over years:
1. Install "Play Axis" from AppSource
2. **Field**: `Investments[Year]`
3. Users can press play to watch the fund grow from 1998 to 2025

---

## 8. Data Refresh & Publishing

### 8.1 Data Source Connection
- **Option A**: Import NBIM CSV/Excel data manually (updated semi-annually)
- **Option B**: Connect to a database/API if you have structured holdings data
- **Option C**: Use Power Query to scrape/transform NBIM's public data downloads

### 8.2 Power Query Transform Example

```m
let
    Source = Csv.Document(File.Contents("nbim_holdings.csv")),
    PromotedHeaders = Table.PromoteHeaders(Source),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"CompanyName", type text},
        {"Year", Int64.Type},
        {"AssetClass", type text},
        {"Country", type text},
        {"Sector", type text},
        {"ValueNOK", type number},
        {"ShareOfFund", type number}
    }),
    FilteredRows = Table.SelectRows(ChangedTypes, each [Year] = 2025)
in
    FilteredRows
```

### 8.3 Publishing
1. **File** > **Publish** > **Power BI Service**
2. Set up **Scheduled Refresh** if connected to a live data source
3. Create a **Power BI App** for distribution to stakeholders

---

## 9. Sample Data Script

To get started quickly, create sample data in Power Query:

```m
let
    // Top 15 NBIM Holdings (2025 data)
    Source = Table.FromRecords({
        [CompanyName="NVIDIA Corp", AssetClass="Equities", Country="United States", Sector="Technology", ValueNOK=574, ShareOfFund=3.2],
        [CompanyName="Apple Inc", AssetClass="Equities", Country="United States", Sector="Technology", ValueNOK=497, ShareOfFund=2.8],
        [CompanyName="Microsoft Corp", AssetClass="Equities", Country="United States", Sector="Technology", ValueNOK=459, ShareOfFund=2.6],
        [CompanyName="Alphabet Inc", AssetClass="Equities", Country="United States", Sector="Technology", ValueNOK=439, ShareOfFund=2.5],
        [CompanyName="Amazon.com Inc", AssetClass="Equities", Country="United States", Sector="Consumer Discretionary", ValueNOK=308, ShareOfFund=1.7],
        [CompanyName="Taiwan Semiconductor", AssetClass="Equities", Country="Taiwan", Sector="Technology", ValueNOK=229, ShareOfFund=1.3],
        [CompanyName="Broadcom Inc", AssetClass="Equities", Country="United States", Sector="Technology", ValueNOK=216, ShareOfFund=1.2],
        [CompanyName="Meta Platforms Inc", AssetClass="Equities", Country="United States", Sector="Technology", ValueNOK=196, ShareOfFund=1.1],
        [CompanyName="Tesla Inc", AssetClass="Equities", Country="United States", Sector="Consumer Discretionary", ValueNOK=161, ShareOfFund=0.9],
        [CompanyName="Eli Lilly & Co", AssetClass="Equities", Country="United States", Sector="Health Care", ValueNOK=121, ShareOfFund=0.7],
        [CompanyName="Berkshire Hathaway", AssetClass="Equities", Country="United States", Sector="Financials", ValueNOK=116, ShareOfFund=0.6],
        [CompanyName="JPMorgan Chase", AssetClass="Equities", Country="United States", Sector="Financials", ValueNOK=113, ShareOfFund=0.6],
        [CompanyName="ASML Holding NV", AssetClass="Equities", Country="Netherlands", Sector="Technology", ValueNOK=96, ShareOfFund=0.5],
        [CompanyName="Tencent Holdings", AssetClass="Equities", Country="China", Sector="Technology", ValueNOK=95, ShareOfFund=0.5],
        [CompanyName="Samsung Electronics", AssetClass="Equities", Country="South Korea", Sector="Technology", ValueNOK=94, ShareOfFund=0.5]
    }),
    AddYear = Table.AddColumn(Source, "Year", each 2025, Int64.Type)
in
    AddYear
```

---

## 10. FigJam Design Reference

A FigJam diagram of the dashboard layout has been created for visual reference:

**Claim your FigJam diagram**: [Open in FigJam](https://www.figma.com/online-whiteboard/create-diagram/b2274e7f-851f-4c4d-9f39-3070ebb5c2de?utm_source=claude&utm_content=edit_in_figjam)

This diagram shows the component hierarchy and layout flow for the Power BI dashboard.

---

## Quick Start Checklist

- [ ] Download/prepare NBIM holdings data
- [ ] Create data model with fact and dimension tables
- [ ] Set up relationships between tables
- [ ] Create DAX measures (Total Value, Counts, Share %, Rankings)
- [ ] Import the custom dark theme JSON
- [ ] Build the treemap as the main visual
- [ ] Add KPI cards across the top
- [ ] Create year and asset class slicers
- [ ] Build the top holdings table
- [ ] Add sector donut and country bar charts
- [ ] Configure cross-filtering and drill-through
- [ ] Add tooltips and bookmarks
- [ ] Test with sample data, then connect real data
- [ ] Publish to Power BI Service
