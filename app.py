from __future__ import annotations

import html
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = ROOT / "data" / "cleaned_student_data.csv"
SUBJECT_COLUMNS = {
    "Math": "Subject_Math",
    "Python": "Subject_Python",
    "DBMS": "Subject_DBMS",
    "AI": "Subject_AI",
}
SCORE_COLUMNS = list(SUBJECT_COLUMNS.values())
REQUIRED_COLUMNS = [
    "Student_ID",
    "Attendance_Percent",
    "Study_Hours_Per_Week",
    *SCORE_COLUMNS,
]
FEATURE_COLUMNS = [
    "Assignment_Score",
    "Internal_Marks",
    "Participation_Score",
    "Previous_Semester_Score",
]
PALETTE = {
    "navy": "#172554",
    "blue": "#4f6df5",
    "teal": "#16a995",
    "green": "#159a76",
    "amber": "#e9a23b",
    "red": "#e26666",
    "muted": "#7b879a",
}
LEVEL_COLORS = {
    "High": PALETTE["green"],
    "Medium": PALETTE["amber"],
    "Needs Improvement": PALETTE["red"],
}

st.set_page_config(
    page_title="ScholarView | Academic analytics",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #172554;
            --muted: #748198;
            --canvas: #f4f6fb;
            --accent: #4f6df5;
        }
        .stApp {
            background: var(--canvas);
            color: var(--ink);
            font-family: 'DM Sans', 'Segoe UI', sans-serif;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stMainBlockContainer"] {
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        section[data-testid="stSidebar"] {
            background: #101a2d;
            border-right: 1px solid rgba(255,255,255,.07);
        }
        section[data-testid="stSidebar"] * { color: #e7edf7; }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #aab6cb;
        }
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #cbd5e1;
            font-size: .82rem;
            font-weight: 600;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="input"] > div {
            background: #1b2940;
            border-color: #31415b;
        }
        section[data-testid="stSidebar"] [data-baseweb="tag"] {
            background: #31435f !important;
            border: 1px solid #465a76 !important;
            color: #e7edf7 !important;
        }
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
            background: #1b2940;
            border: 1px dashed #42516a;
            border-radius: 12px;
            padding: 8px;
        }
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
            background: #f2f5fb;
            color: #172554;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 11px;
            padding: 4px 0 24px;
        }
        .brand-mark {
            display: grid;
            width: 38px;
            height: 38px;
            place-items: center;
            border-radius: 12px;
            background: linear-gradient(140deg, #6b83ff, #4560ed);
            color: white;
            font: 800 17px 'Manrope', 'Segoe UI', sans-serif;
            box-shadow: 0 7px 20px rgba(79,109,245,.25);
        }
        .brand-name { color: #fff; font: 800 17px 'Manrope', sans-serif; }
        .brand-caption { color: #8998b2; font-size: 11px; margin-top: 1px; }
        .side-section {
            color: #8290a8;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: .13em;
            margin: 20px 0 9px;
            text-transform: uppercase;
        }
        .sidebar-note {
            border: 1px solid #2b3b54;
            border-radius: 12px;
            color: #afbdd1;
            font-size: 12px;
            line-height: 1.55;
            margin-top: 25px;
            padding: 13px;
        }
        .page-kicker {
            color: var(--accent);
            font-size: 11px;
            font-weight: 700;
            letter-spacing: .12em;
            margin-bottom: 7px;
            text-transform: uppercase;
        }
        .page-title {
            color: var(--ink);
            font: 800 clamp(27px, 3vw, 36px)/1.15 'Manrope', 'Segoe UI', sans-serif;
            letter-spacing: -.04em;
            margin: 0;
        }
        .page-subtitle { color: var(--muted); font-size: 14px; margin-top: 8px; }
        .status-pill {
            background: #e7f7f1;
            border: 1px solid #d2f0e5;
            border-radius: 999px;
            color: #12815f;
            display: inline-block;
            font-size: 11px;
            font-weight: 700;
            padding: 7px 11px;
            white-space: nowrap;
        }
        [data-testid="stMetric"] {
            background: #fff;
            border: 1px solid #e8ecf3;
            border-radius: 16px;
            box-shadow: 0 5px 18px rgba(35,51,86,.035);
            padding: 13px 12px;
        }
        [data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: 10px;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: var(--ink);
            font: 800 22px 'Manrope', 'Segoe UI', sans-serif;
            white-space: nowrap;
        }
        .section-heading {
            color: var(--ink);
            font: 700 17px 'Manrope', 'Segoe UI', sans-serif;
            letter-spacing: -.02em;
        }
        .section-caption { color: var(--muted); font-size: 12px; margin-top: 3px; }
        .insight-card {
            align-items: flex-start;
            background: linear-gradient(110deg, #edf2ff, #f8faff);
            border: 1px solid #dfe7ff;
            border-radius: 14px;
            color: #405174;
            display: flex;
            font-size: 13px;
            gap: 12px;
            line-height: 1.6;
            margin: 18px 0 21px;
            padding: 14px 17px;
        }
        .insight-icon {
            align-items: center;
            background: #dce5ff;
            border-radius: 9px;
            color: #4662e8;
            display: flex;
            flex: 0 0 28px;
            font-size: 14px;
            height: 28px;
            justify-content: center;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #fff;
            border-color: #e8ecf3;
            border-radius: 16px;
            box-shadow: 0 5px 18px rgba(35,51,86,.035);
        }
        div[data-testid="stTabs"] button {
            color: #77849a;
            font-weight: 600;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #405fe9;
        }
        div[data-testid="stDownloadButton"] button {
            border-radius: 10px;
            font-weight: 600;
        }
        .footer {
            border-top: 1px solid #e3e8f0;
            color: #8994a6;
            font-size: 11px;
            margin-top: 28px;
            padding-top: 16px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_student_data(uploaded_bytes: bytes | None = None) -> pd.DataFrame:
    if uploaded_bytes is None:
        if not DEFAULT_DATA_PATH.is_file():
            raise FileNotFoundError(
                f"Default dataset not found: {DEFAULT_DATA_PATH}"
            )
        frame = pd.read_csv(DEFAULT_DATA_PATH)
    else:
        frame = pd.read_csv(BytesIO(uploaded_bytes))

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame]
    if missing_columns:
        raise ValueError(
            "The CSV is missing required columns: " + ", ".join(missing_columns)
        )
    if frame.empty:
        raise ValueError("The CSV does not contain any student records.")

    numeric_columns = [
        column
        for column in frame.columns
        if column in REQUIRED_COLUMNS[1:]
        or column in FEATURE_COLUMNS
    ]
    for column in numeric_columns:
        if column in frame:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    invalid_columns = [
        column
        for column in numeric_columns
        if column in frame
        and (frame[column].isna() | ~frame[column].between(-1e100, 1e100)).any()
    ]
    if invalid_columns:
        raise ValueError(
            "Numeric fields contain missing or invalid values: "
            + ", ".join(invalid_columns)
        )

    bounded_columns = [
        "Attendance_Percent",
        *SCORE_COLUMNS,
        *(column for column in FEATURE_COLUMNS if column in frame),
    ]
    out_of_range = [
        column
        for column in bounded_columns
        if not frame[column].between(0, 100).all()
    ]
    if out_of_range:
        raise ValueError(
            "Attendance and subject scores must be between 0 and 100: "
            + ", ".join(out_of_range)
        )
    if (frame["Study_Hours_Per_Week"] < 0).any():
        raise ValueError("Study_Hours_Per_Week cannot contain negative values.")
    if frame["Student_ID"].isna().any():
        raise ValueError("Student_ID cannot be empty.")

    frame["Student_ID"] = frame["Student_ID"].astype(str).str.strip()
    if frame["Student_ID"].eq("").any():
        raise ValueError("Student_ID cannot be empty.")
    if frame["Student_ID"].duplicated().any():
        raise ValueError("Student_ID values must be unique.")
    frame["Overall_Average"] = frame[SCORE_COLUMNS].mean(axis=1)
    frame["Learning_Gap_Subject"] = (
        frame[SCORE_COLUMNS]
        .idxmin(axis=1)
        .str.removeprefix("Subject_")
    )
    frame["Performance_Level"] = pd.cut(
        frame["Overall_Average"],
        bins=[-float("inf"), 50, 75, float("inf")],
        labels=["Needs Improvement", "Medium", "High"],
        right=False,
    ).astype(str)
    frame["Risk_Status"] = frame["Overall_Average"].lt(60).map(
        {True: "At Risk", False: "On Track"}
    )
    return frame


def chart_layout(fig: go.Figure, height: int = 310) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=16, t=15, b=14),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#64718a", size=11),
        hoverlabel=dict(
            bgcolor="#172554",
            bordercolor="#172554",
            font=dict(color="#ffffff", family="DM Sans, sans-serif"),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#edf0f5",
        zeroline=False,
        linecolor="#e8ecf3",
        tickfont=dict(color="#7b879a", size=10),
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        linecolor="#e8ecf3",
        tickfont=dict(color="#596780", size=11),
    )
    return fig


def score_band(score: float) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Needs Improvement"


def render_overview(frame: pd.DataFrame) -> None:
    average_score = frame["Overall_Average"].mean()
    risk_count = int(frame["Risk_Status"].eq("At Risk").sum())
    attendance = frame["Attendance_Percent"].mean()
    risk_percent = risk_count / len(frame) * 100

    metrics = st.columns(4)
    metrics[0].metric("Students", f"{len(frame):,}")
    metrics[1].metric(
        "Avg. score",
        f"{average_score:.1f}%",
        delta=f"{average_score - 60:+.1f} pts vs. risk threshold",
        delta_color="normal",
    )
    metrics[2].metric(
        f"At risk · {risk_percent:.0f}%",
        f"{risk_count:,}",
    )
    metrics[3].metric("Attendance avg.", f"{attendance:.1f}%")

    subject_means = frame[SCORE_COLUMNS].mean().rename(
        lambda column: column.removeprefix("Subject_")
    )
    lowest_subject = subject_means.idxmin()
    lowest_score = subject_means.min()
    below_threshold = int(frame[SUBJECT_COLUMNS[lowest_subject]].lt(60).sum())
    st.markdown(
        f"""
        <div class="insight-card">
          <div class="insight-icon">i</div>
          <div><strong>{lowest_subject} is the biggest learning opportunity.</strong>
          Its cohort average is {lowest_score:.1f}%, with {below_threshold}
          {('student' if below_threshold == 1 else 'students')} below the 60% support threshold.
          Use the filters to find students who may benefit from targeted help.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    subject_frame = (
        subject_means.rename("Average score")
        .rename_axis("Subject")
        .reset_index()
    )
    subject_frame["Band"] = subject_frame["Average score"].map(score_band)

    left, right = st.columns([1.45, 1])
    with left:
        with st.container(border=True):
            st.markdown(
                '<div class="section-heading">Subject performance</div>'
                '<div class="section-caption">Average score by subject · dashed line marks 60%</div>',
                unsafe_allow_html=True,
            )
            subject_chart = px.bar(
                subject_frame.sort_values("Average score"),
                x="Average score",
                y="Subject",
                orientation="h",
                color="Band",
                color_discrete_map=LEVEL_COLORS,
                text="Average score",
                hover_data={"Band": False, "Average score": ":.1f"},
            )
            subject_chart.update_traces(
                texttemplate="%{text:.1f}%",
                textposition="outside",
                cliponaxis=False,
                marker_line_width=0,
            )
            subject_chart.update_xaxes(range=[0, 112], ticksuffix="%")
            subject_chart.add_vline(
                x=60,
                line_dash="dash",
                line_color="#98a4b7",
                line_width=1,
                annotation_text="Support threshold",
                annotation_position="top",
                annotation_font_size=9,
                annotation_font_color="#8490a2",
            )
            subject_chart.update_layout(
                showlegend=False,
                yaxis_title=None,
                xaxis_title=None,
                height=300,
            )
            st.plotly_chart(
                chart_layout(subject_chart, 300),
                width="stretch",
                config={"displayModeBar": False},
            )

    with right:
        with st.container(border=True):
            st.markdown(
                '<div class="section-heading">Performance mix</div>'
                '<div class="section-caption">Students grouped by overall average</div>',
                unsafe_allow_html=True,
            )
            level_order = ["High", "Medium", "Needs Improvement"]
            level_counts = (
                frame["Performance_Level"]
                .value_counts()
                .reindex(level_order, fill_value=0)
                .rename_axis("Level")
                .reset_index(name="Students")
            )
            level_chart = px.pie(
                level_counts,
                names="Level",
                values="Students",
                hole=0.72,
                color="Level",
                color_discrete_map=LEVEL_COLORS,
                category_orders={"Level": level_order},
            )
            level_chart.update_traces(
                textinfo="percent",
                textfont_size=11,
                marker=dict(line=dict(color="#ffffff", width=4)),
                hovertemplate="%{label}: %{value} students (%{percent})<extra></extra>",
            )
            level_chart.update_layout(
                height=300,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.08,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10),
                ),
                annotations=[
                    dict(
                        text=f"<b>{len(frame)}</b><br><span style='font-size:10px'>students</span>",
                        x=0.5,
                        y=0.5,
                        showarrow=False,
                        font=dict(size=22, color=PALETTE["navy"]),
                    )
                ],
            )
            st.plotly_chart(
                chart_layout(level_chart, 300),
                width="stretch",
                config={"displayModeBar": False},
            )

    lower_left, lower_right = st.columns([1.45, 1])
    with lower_left:
        with st.container(border=True):
            st.markdown(
                '<div class="section-heading">Attendance & achievement</div>'
                '<div class="section-caption">Explore how attendance relates to overall results</div>',
                unsafe_allow_html=True,
            )
            scatter = px.scatter(
                frame,
                x="Attendance_Percent",
                y="Overall_Average",
                color="Performance_Level",
                color_discrete_map=LEVEL_COLORS,
                category_orders={
                    "Performance_Level": ["High", "Medium", "Needs Improvement"]
                },
                hover_name="Student_ID",
                hover_data={
                    "Attendance_Percent": ":.1f",
                    "Overall_Average": ":.1f",
                    "Study_Hours_Per_Week": ":.1f",
                    "Learning_Gap_Subject": True,
                    "Performance_Level": False,
                },
                opacity=0.78,
            )
            scatter.update_traces(
                marker=dict(size=9, line=dict(width=1, color="#ffffff"))
            )
            scatter.add_hline(
                y=60,
                line_dash="dash",
                line_color="#98a4b7",
                line_width=1,
            )
            scatter.update_layout(
                xaxis_title="Attendance",
                yaxis_title="Overall score",
                xaxis_ticksuffix="%",
                yaxis_ticksuffix="%",
                legend_title=None,
                legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
                height=320,
            )
            st.plotly_chart(
                chart_layout(scatter, 320),
                width="stretch",
                config={"displayModeBar": False},
            )

    with lower_right:
        with st.container(border=True):
            st.markdown(
                '<div class="section-heading">Learning gap hotspots</div>'
                '<div class="section-caption">Most common lowest-scoring subject</div>',
                unsafe_allow_html=True,
            )
            gap_counts = (
                frame["Learning_Gap_Subject"]
                .value_counts()
                .reindex(list(SUBJECT_COLUMNS), fill_value=0)
                .rename_axis("Subject")
                .reset_index(name="Students")
                .sort_values("Students")
            )
            gap_chart = px.bar(
                gap_counts,
                x="Students",
                y="Subject",
                orientation="h",
                text="Students",
                color_discrete_sequence=[PALETTE["blue"]],
            )
            gap_chart.update_traces(
                textposition="outside",
                cliponaxis=False,
                marker=dict(
                    cornerradius=7,
                    line=dict(width=0),
                ),
            )
            gap_chart.update_xaxes(
                range=[0, max(1, int(gap_counts["Students"].max() * 1.25))],
                title=None,
                dtick=max(1, round(len(frame) / 10)),
            )
            gap_chart.update_layout(
                yaxis_title=None,
                showlegend=False,
                height=320,
            )
            st.plotly_chart(
                chart_layout(gap_chart, 320),
                width="stretch",
                config={"displayModeBar": False},
            )


def render_students(frame: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-heading">Student records</div>'
        '<div class="section-caption">Search, sort and export the students in the selected cohort.</div>',
        unsafe_allow_html=True,
    )
    search = st.text_input(
        "Search by student ID",
        placeholder="For example, S014",
        label_visibility="collapsed",
    )
    records = frame.copy()
    if search.strip():
        records = records[
            records["Student_ID"].str.contains(search.strip(), case=False, na=False)
        ]

    display_columns = [
        "Student_ID",
        "Performance_Level",
        "Overall_Average",
        "Risk_Status",
        "Attendance_Percent",
        "Study_Hours_Per_Week",
        "Learning_Gap_Subject",
        *SCORE_COLUMNS,
    ]
    display_names = {
        "Student_ID": "Student ID",
        "Performance_Level": "Performance",
        "Overall_Average": "Overall score",
        "Risk_Status": "Support status",
        "Attendance_Percent": "Attendance %",
        "Study_Hours_Per_Week": "Study hours / week",
        "Learning_Gap_Subject": "Focus subject",
        "Subject_Math": "Math",
        "Subject_Python": "Python",
        "Subject_DBMS": "DBMS",
        "Subject_AI": "AI",
    }
    records = records[display_columns].rename(columns=display_names)
    st.caption(f"Showing {len(records):,} of {len(frame):,} students")
    st.dataframe(
        records,
        width="stretch",
        hide_index=True,
        height=480,
        column_config={
            "Overall score": st.column_config.NumberColumn(format="%.1f%%"),
            "Attendance %": st.column_config.NumberColumn(format="%.1f%%"),
            "Study hours / week": st.column_config.NumberColumn(format="%.1f"),
            "Math": st.column_config.NumberColumn(format="%.1f"),
            "Python": st.column_config.NumberColumn(format="%.1f"),
            "DBMS": st.column_config.NumberColumn(format="%.1f"),
            "AI": st.column_config.NumberColumn(format="%.1f"),
        },
    )
    st.download_button(
        "Download filtered records",
        data=records.to_csv(index=False).encode("utf-8"),
        file_name="student_performance_filtered.csv",
        mime="text/csv",
    )


def render_student_profile(frame: pd.DataFrame) -> None:
    st.markdown(
        '<div class="section-heading">Student profile</div>'
        '<div class="section-caption">A closer look at academic strengths and learning opportunities.</div>',
        unsafe_allow_html=True,
    )
    student_id = st.selectbox("Choose a student", frame["Student_ID"].tolist())
    student = frame.loc[frame["Student_ID"].eq(student_id)].iloc[0]
    left, right = st.columns([1.2, 1])

    with left:
        with st.container(border=True):
            st.markdown(
                f'<div class="section-heading">{html.escape(student_id)}</div>'
                f'<div class="section-caption">{student["Performance_Level"]} performer · {student["Risk_Status"]}</div>',
                unsafe_allow_html=True,
            )
            radar = go.Figure()
            radar.add_trace(
                go.Scatterpolar(
                    r=[student[column] for column in SCORE_COLUMNS],
                    theta=list(SUBJECT_COLUMNS),
                    fill="toself",
                    fillcolor="rgba(79,109,245,.16)",
                    line=dict(color=PALETTE["blue"], width=3),
                    marker=dict(size=7, color=PALETTE["blue"]),
                    hovertemplate="%{theta}: %{r:.1f}%<extra></extra>",
                )
            )
            radar.update_layout(
                height=370,
                margin=dict(l=35, r=35, t=25, b=25),
                paper_bgcolor="rgba(0,0,0,0)",
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                        ticksuffix="%",
                        gridcolor="#e9edf4",
                        linecolor="#e9edf4",
                        tickfont=dict(size=9, color="#8490a2"),
                    ),
                    angularaxis=dict(
                        gridcolor="#e9edf4",
                        linecolor="#e9edf4",
                        tickfont=dict(size=11, color="#53617a"),
                    ),
                ),
                showlegend=False,
            )
            st.plotly_chart(
                radar,
                width="stretch",
                config={"displayModeBar": False},
            )

    with right:
        profile_metrics = st.columns(2)
        profile_metrics[0].metric("Overall score", f'{student["Overall_Average"]:.1f}%')
        profile_metrics[1].metric("Attendance", f'{student["Attendance_Percent"]:.1f}%')
        profile_metrics[0].metric("Study time", f'{student["Study_Hours_Per_Week"]:.1f} hrs/wk')
        profile_metrics[1].metric("Focus subject", student["Learning_Gap_Subject"])

        if all(column in frame for column in FEATURE_COLUMNS):
            with st.container(border=True):
                st.markdown(
                    '<div class="section-heading">Engagement & coursework</div>'
                    '<div class="section-caption">Individual scores on a 100-point scale</div>',
                    unsafe_allow_html=True,
                )
                feature_names = {
                    "Assignment_Score": "Assignments",
                    "Internal_Marks": "Internal marks",
                    "Participation_Score": "Participation",
                    "Previous_Semester_Score": "Previous semester",
                }
                feature_frame = pd.DataFrame(
                    {
                        "Measure": [feature_names[column] for column in FEATURE_COLUMNS],
                        "Score": [student[column] for column in FEATURE_COLUMNS],
                    }
                ).sort_values("Score")
                feature_chart = px.bar(
                    feature_frame,
                    x="Score",
                    y="Measure",
                    orientation="h",
                    text="Score",
                    color_discrete_sequence=[PALETTE["teal"]],
                )
                feature_chart.update_traces(
                    texttemplate="%{text:.0f}",
                    textposition="outside",
                    cliponaxis=False,
                )
                feature_chart.update_xaxes(range=[0, 115], title=None, ticksuffix="%")
                feature_chart.update_layout(
                    height=285,
                    yaxis_title=None,
                    showlegend=False,
                )
                st.plotly_chart(
                    chart_layout(feature_chart, 285),
                    width="stretch",
                    config={"displayModeBar": False},
                )


def main() -> None:
    apply_styles()

    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
              <div class="brand-mark">S</div>
              <div><div class="brand-name">ScholarView</div>
              <div class="brand-caption">Academic intelligence</div></div>
            </div>
            <div class="side-section">Your data</div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload a student CSV",
            type=["csv"],
            help="The file must include student ID, attendance, study hours and four subject scores.",
        )
        st.markdown('<div class="side-section">Cohort filters</div>', unsafe_allow_html=True)
        performance_filter = st.multiselect(
            "Performance level",
            ["High", "Medium", "Needs Improvement"],
            default=["High", "Medium", "Needs Improvement"],
        )
        risk_filter = st.selectbox("Support status", ["All", "At Risk", "On Track"])
        subject_filter = st.selectbox(
            "Focus subject",
            ["All", *SUBJECT_COLUMNS],
        )

    try:
        students = load_student_data(
            uploaded_file.getvalue() if uploaded_file is not None else None
        )
    except (FileNotFoundError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
        st.error(f"Unable to load student data: {error}")
        st.stop()

    with st.sidebar:
        minimum_attendance = float(students["Attendance_Percent"].min())
        maximum_attendance = float(students["Attendance_Percent"].max())
        attendance_range = st.slider(
            "Attendance range",
            min_value=0.0,
            max_value=100.0,
            value=(minimum_attendance, maximum_attendance),
            step=0.1,
            format="%.1f%%",
        )
        search_id = st.text_input("Student ID", placeholder="Search cohort")
        st.markdown(
            f"""
            <div class="sidebar-note">
              <strong>How to read this dashboard</strong><br>
              At risk means an overall average below 60%. Performance bands use
              the project thresholds: High ≥ 75, Medium ≥ 50, and Needs Improvement &lt; 50.
            </div>
            """,
            unsafe_allow_html=True,
        )

    cohort = students[
        students["Performance_Level"].isin(performance_filter)
        & students["Attendance_Percent"].between(*attendance_range)
    ]
    if risk_filter != "All":
        cohort = cohort[cohort["Risk_Status"].eq(risk_filter)]
    if subject_filter != "All":
        cohort = cohort[cohort["Learning_Gap_Subject"].eq(subject_filter)]
    if search_id.strip():
        cohort = cohort[
            cohort["Student_ID"].str.contains(search_id.strip(), case=False, na=False)
        ]

    header_left, header_right = st.columns([1, 0.25], vertical_alignment="center")
    with header_left:
        st.markdown(
            '<div class="page-kicker">LEARNING OUTCOMES · LIVE COHORT</div>'
            '<h1 class="page-title">Academic overview</h1>'
            '<div class="page-subtitle">A clear view of student progress, engagement and where support matters most.</div>',
            unsafe_allow_html=True,
        )
    with header_right:
        source_label = (
            html.escape(uploaded_file.name)
            if uploaded_file is not None
            else "Sample dataset"
        )
        st.markdown(
            f'<div style="text-align:right"><span class="status-pill">● &nbsp;{source_label}</span></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    if cohort.empty:
        st.warning("No students match these filters. Adjust the sidebar filters to see results.")
        st.stop()

    overview_tab, students_tab, profile_tab = st.tabs(
        ["Overview", "Student records", "Student profile"]
    )
    with overview_tab:
        render_overview(cohort)
    with students_tab:
        render_students(cohort)
    with profile_tab:
        render_student_profile(cohort)

    st.markdown(
        '<div class="footer">ScholarView · Student data is processed locally for this dashboard. '
        'Use cohort filters to explore the students represented in each view.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
