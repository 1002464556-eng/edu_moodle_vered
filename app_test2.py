import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="משימות מודל - מחוז והעיר ירושלים", layout="wide", page_icon="🏆")

# טעינת נתונים חכמה שגם מנקה רווחים נסתרים!
@st.cache_data
def load_data():
    try:
        df1 = pd.read_csv('מתמטיקה+מדעים _ מחוז ועיר 16.03.csv', encoding='utf-8-sig')
        df2 = pd.read_csv('ללא קורסים.csv', encoding='utf-8-sig')
    except:
        df1 = pd.read_csv('מתמטיקה+מדעים _ מחוז ועיר 16.03.csv', encoding='cp1255')
        df2 = pd.read_csv('ללא קורסים.csv', encoding='cp1255')
        
    # ניקוי רווחים מיותרים שגורמים לנתונים להיעלם
    cols_to_strip_df1 = ['תחום', 'מחוז תקשוב', 'שם מפקח']
    for col in cols_to_strip_df1:
        if col in df1.columns:
            df1[col] = df1[col].astype(str).str.strip()
            
    cols_to_strip_df2 = ['תחום', 'מחוז תקשוב', 'מפקח']
    for col in cols_to_strip_df2:
        if col in df2.columns:
            df2[col] = df2[col].astype(str).str.strip()
            
    return df1, df2

df1, df2 = load_data()

# כותרת ראשית ותת כותרת
st.title("משימות מודל - מחוז והעיר ירושלים")
st.markdown("### יעד לחודש מרץ : 8 משימות במדעים | 17 משימות במתמטיקה")
st.divider()

# בחירת מחוז בצד
st.sidebar.header("הגדרות תצוגה")
district = st.sidebar.selectbox("בחר/י מחוז למיקוד:", ['ירושלים', 'העיר ירושלים'])

# סינון הנתונים לפי המחוז שנבחר
df1_dist = df1[df1['מחוז תקשוב'] == district]
df2_dist = df2[df2['מחוז תקשוב'] == district]

st.header(f"📌 תמונת מצב - מחוז {district}")

# חישוב נתונים כלליים
def calc_macro(df, domain):
    d = df[df['תחום'] == domain]
    if d.empty or d['מספר תלמידים בשכבה'].sum() == 0:
        return 0, 0
    # כדי למנוע חלוקה באפס או שגיאות, נחשב רק אם יש נתונים
    total_students = d['מספר תלמידים בשכבה'].sum()
    if total_students > 0:
        pct_active = (d['תלמידים שביצעו משימה אחת לפחות'].sum() / total_students) * 100
    else:
        pct_active = 0
    avg_tasks = d['ממוצע משימות לתלמיד- כלל שכבתי'].mean()
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
# נסנן רק מפקחים קיימים למחוז הנבחר
supervisors = df1_dist['שם מפקח'].dropna().unique()
# נמחק ערכים ריקים (nan) מרשימת המפקחים
supervisors = [s for s in supervisors if s.lower() != 'nan']
supervisor = st.selectbox("בחר/י מפקח להצגת נתונים:", supervisors)

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

# פונקציות עיצוב שצובעות את שתי העמודות (כולל בדיקה שהערך קיים)
def style_math_row(row):
    val = row['ממוצע משימות לתלמיד- כלל שכבתי']
    try:
        val = float(val)
        if pd.isna(val): 
            color = ''
        elif val < 5: 
            color = 'background-color: #ffcccc; color: black;' # אדום
        elif 5 <= val <= 15: 
            color = 'background-color: #ffffcc; color: black;' # צהוב
        else: 
            color = 'background-color: #ccffcc; color: black;' # ירוק
    except:
        color = ''
    
    return [color if col in ['מוסד', 'ממוצע משימות לתלמיד- כלל שכבתי'] else '' for col in row.index]

def style_sci_row(row):
    val = row['ממוצע משימות לתלמיד- כלל שכבתי']
    try:
        val = float(val)
        if pd.isna(val): 
            color = ''
        elif val < 2: 
            color = 'background-color: #ffcccc; color: black;' # אדום
        elif 2 <= val <= 4: 
            color = 'background-color: #ffffcc; color: black;' # צהוב
        else: 
            color = 'background-color: #ccffcc; color: black;' # ירוק
    except:
        color = ''
        
    return [color if col in ['מוסד', 'ממוצע משימות לתלמיד- כלל שכבתי'] else '' for col in row.index]

cols_to_show = ['מוסד', 'רשות', 'מספר תלמידים בשכבה', 'תלמידים שביצעו משימה אחת לפחות', 'ממוצע משימות לתלמיד- כלל שכבתי']

with tab1:
    df_math = df1_sup[df1_sup['תחום'] == 'מתמטיקה'][cols_to_show]
    st.dataframe(df_math.style.apply(style_math_row, axis=1), use_container_width=True, hide_index=True)

with tab2:
    df_sci = df1_sup[df1_sup['תחום'] == 'מדעים'][cols_to_show]
    st.dataframe(df_sci.style.apply(style_sci_row, axis=1), use_container_width=True, hide_index=True)

st.divider()

st.header("🚨 בתי ספר הדורשים התערבות (ללא קורסים)")
df2_sup = df2_dist[df2_dist['מפקח'] == supervisor] 
math_no_course = df2_sup[df2_sup['תחום'] == 'מתמטיקה']
sci_no_course = df2_sup[df2_sup['תחום'] == 'מדעים']

col_no1, col_no2 = st.columns(2)
with col_no1:
    with st.expander(f"מתמטיקה: {len(math_no_course)} מוסדות"):
        st.dataframe(math_no_course[['מוסד', 'רשות']], hide_index=True, use_container_width=True)
with col_no2:
    with st.expander(f"מדעים: {len(sci_no_course)} מוסדות"):
        st.dataframe(sci_no_course[['מוסד', 'רשות']], hide_index=True, use_container_width=True)