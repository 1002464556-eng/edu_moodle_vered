import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="משימות מודל - מחוז והעיר ירושלים", layout="wide", page_icon="🏆")

@st.cache_data
def load_and_process_data():
    # 1. טעינת קובץ ההחרגות וניקוי סמלי המוסד
    try:
        excluded_df = pd.read_csv('מוסדות_להחרגה.csv', encoding='utf-8-sig')
        excluded_ids = excluded_df['סמל מוסד'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().tolist()
    except:
        excluded_ids = []

    # 2. פונקציה שעושה את כל עבודת האקסל שלך אוטומטית!
    def process_moodle_file(filename, domain):
        try:
            df = pd.read_csv(filename, encoding='utf-8-sig')
        except:
            df = pd.read_csv(filename, encoding='cp1255')
        
        # מחיקת שורה 2 המיותרת מהמערכת (אינדקס 0)
        df = df.iloc[1:].reset_index(drop=True)
        df.columns = df.columns.str.strip()
        
        # הפיכת העמודות למספרים כדי שאפשר יהיה לחשב
        col_i, col_j, col_k = df.columns[8], df.columns[9], df.columns[10]
        for col in [col_i, col_j, col_k]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # יצירת העמודות החדשות והחישובים שלך
        df['תלמידים שלא ביצעו כלל משימות'] = df[col_i] - df[col_j]
        df['ממוצע משימות לכלל השכבה'] = df.apply(
            lambda row: (row[col_j] * row[col_k]) / row[col_i] if row[col_i] > 0 else 0, axis=1
        )
        df['ממוצע משימות לכלל השכבה'] = df['ממוצע משימות לכלל השכבה'].round(2)
        df['תחום'] = domain
        
        # מחיקת בתי הספר המוחרגים לפי סמל מוסד
        if 'סמל מוסד' in df.columns:
            clean_ids = df['סמל מוסד'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df = df[~clean_ids.isin(excluded_ids)]
            
        return df

    # 3. הפעלת הרובוט על מתמטיקה ומדעים וחיבור שלהם יחד
    df_math = process_moodle_file('מתמטיקה מודל.csv', 'מתמטיקה')
    df_sci = process_moodle_file('מדעים מודל.csv', 'מדעים')
    df1 = pd.concat([df_math, df_sci], ignore_index=True)
    
    # 4. טיפול בקובץ "ללא קורסים"
    try:
        df2 = pd.read_csv('ללא קורסים.csv', encoding='utf-8-sig')
    except:
        df2 = pd.read_csv('ללא קורסים.csv', encoding='cp1255')
        
    # מחיקת מוחרגים מקובץ ללא קורסים
    if 'סמל מוסד' in df2.columns:
        clean_ids2 = df2['סמל מוסד'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        df2 = df2[~clean_ids2.isin(excluded_ids)]
        
    # סינון רק את מי שקיבל 50% ומטה
    col_s = df2.columns[18]
    df2['אחוז_נקי'] = df2[col_s].astype(str).str.replace('%', '', regex=False)
    df2['אחוז_נקי'] = pd.to_numeric(df2['אחוז_נקי'], errors='coerce').fillna(100)
    df2 = df2[df2['אחוז_נקי'] <= 50]
    
    # ניקוי רווחים משמות המפקחים כדי שהחיפוש יעבוד חלק
    for col in ['מחוז תקשוב', 'שם מפקח', 'מפקח']:
        if col in df1.columns: df1[col] = df1[col].astype(str).str.strip()
        if col in df2.columns: df2[col] = df2[col].astype(str).str.strip()
        
    return df1, df2

df1, df2 = load_and_process_data()

st.title("משימות מודל - מחוז והעיר ירושלים (טסט אוטומטי)")
st.markdown("### יעד לחודש מרץ : 8 משימות במדעים | 17 משימות במתמטיקה")
st.divider()

st.sidebar.header("הגדרות תצוגה")
district = st.sidebar.selectbox("בחר/י מחוז למיקוד:", ['ירושלים', 'העיר ירושלים'])

df1_dist = df1[df1['מחוז תקשוב'] == district]
df2_dist = df2[df2['מחוז תקשוב'] == district]

st.header(f"📌 תמונת מצב - מחוז {district}")

def calc_macro(df, domain):
    d = df[df['תחום'] == domain]
    if d.empty or d.iloc[:, 8].sum() == 0:
        return 0, 0
    total_students = d.iloc[:, 8].sum()
    pct_active = (d.iloc[:, 9].sum() / total_students) * 100 if total_students > 0 else 0
    avg_tasks = d['ממוצע משימות לכלל השכבה'].mean()
    return pct_active, avg_tasks

math_pct, math_avg = calc_macro(df1_dist, 'מתמטיקה')
sci_pct, sci_avg = calc_macro(df1_dist, 'מדעים')

col1, col2 = st.columns(2)
with col1:
    st.subheader("📐 מתמטיקה")
    st.metric("אחוז תלמידים פעילים", f"{math_pct:.1f}%")
    st.metric("ממוצע משימות לשכבה", f"{math_avg:.1f}")

with col2:
    st.subheader("🔬 מדעים")
    st.metric("אחוז תלמידים פעילים", f"{sci_pct:.1f}%")
    st.metric("ממוצע משימות לשכבה", f"{sci_avg:.1f}")

st.divider()

st.header("👤 פילוח לפי מפקחים")
supervisors = [s for s in df1_dist['שם מפקח'].dropna().unique() if s.lower() != 'nan']
supervisor = st.selectbox("בחר/י מפקח להצגת נתונים:", supervisors) if supervisors else ""

if supervisor:
    df1_sup = df1_dist[df1_dist['שם מפקח'] == supervisor]
    math_sup_pct, math_sup_avg = calc_macro(df1_sup, 'מתמטיקה')
    sci_sup_pct, sci_sup_avg = calc_macro(df1_sup, 'מדעים')

    chart_data = pd.DataFrame({
        'מדד': ['אחוז תלמידים פעילים', 'ממוצע משימות לשכבה', 'אחוז תלמידים פעילים ', 'ממוצע משימות לשכבה '],
        'ערך': [math_sup_pct, math_sup_avg, sci_sup_pct, sci_sup_avg],
        'תחום': ['מתמטיקה', 'מתמטיקה', 'מדעים', 'מדעים']
    })

    fig = px.bar(chart_data, x='מדד', y='ערך', color='תחום', text_auto='.1f', 
                 title=f"מדדי ביצוע - בתי הספר באחריות המפקח/ת: {supervisor}", barmode='group')
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📋 פירוט מוסדות (Drill-Down)")
    tab1, tab2 = st.tabs(["📐 בתי ספר - מתמטיקה", "🔬 בתי ספר - מדעים"])

    def style_math_row(row):
        val = row['ממוצע משימות לכלל השכבה']
        try:
            val = float(val)
            if pd.isna(val): color = ''
            elif val < 5: color = 'background-color: #ffcccc; color: black;'
            elif 5 <= val <= 15: color = 'background-color: #ffffcc; color: black;'
            else: color = 'background-color: #ccffcc; color: black;'
        except: color = ''
        return [color if col in ['מוסד', 'ממוצע משימות לכלל השכבה'] else '' for col in row.index]

    def style_sci_row(row):
        val = row['ממוצע משימות לכלל השכבה']
        try:
            val = float(val)
            if pd.isna(val): color = ''
            elif val < 2: color = 'background-color: #ffcccc; color: black;'
            elif 2 <= val <= 4: color = 'background-color: #ffffcc; color: black;'
            else: color = 'background-color: #ccffcc; color: black;'
        except: color = ''
        return [color if col in ['מוסד', 'ממוצע משימות לכלל השכבה'] else '' for col in row.index]

    cols_to_show = ['סמל מוסד', 'מוסד', 'רשות', df1.columns[8], df1.columns[9], 'ממוצע משימות לכלל השכבה']

    with tab1:
        df_math = df1_sup[df1_sup['תחום'] == 'מתמטיקה'][cols_to_show]
        st.dataframe(df_math.style.apply(style_math_row, axis=1), use_container_width=True, hide_index=True)

    with tab2:
        df_sci = df1_sup[df1_sup['תחום'] == 'מדעים'][cols_to_show]
        st.dataframe(df_sci.style.apply(style_sci_row, axis=1), use_container_width=True, hide_index=True)

    st.divider()

    st.header("🚨 בתי ספר הדורשים התערבות (ללא קורסים או מתחת ל-50%)")
    if 'מפקח' in df2.columns:
        df2_sup = df2_dist[df2_dist['מפקח'] == supervisor] 
        math_no_course = df2_sup[df2_sup['תחום'] == 'מתמטיקה']
        sci_no_course = df2_sup[df2_sup['תחום'] == 'מדעים']

        col_no1, col_no2 = st.columns(2)
        with col_no1:
            with st.expander(f"מתמטיקה: {len(math_no_course)} מוסדות"):
                st.dataframe(math_no_course[['סמל מוסד', 'מוסד', 'רשות']], hide_index=True, use_container_width=True)
        with col_no2:
            with st.expander(f"מדעים: {len(sci_no_course)} מוסדות"):
                st.dataframe(sci_no_course[['סמל מוסד', 'מוסד', 'רשות']], hide_index=True, use_container_width=True)
