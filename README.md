# ScholarView — Academic Performance Analytics

ScholarView is an interactive dashboard for exploring student performance, attendance, subject-level learning gaps, and support needs. It includes a sample cohort of 100 students and can also analyze a compatible CSV file.

## Run the dashboard

From this project folder, create and activate a virtual environment, then install the dependencies and start Streamlit:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

If you already have a virtual environment, activate it and run the install and launch commands without creating a new one.

## Share the app online

The app can be hosted on [Streamlit Community Cloud](https://share.streamlit.io/). The hosting service deploys from a GitHub repository; review GitHub's repository visibility before uploading, because a public repository makes its committed source and sample data visible to everyone. The bundled CSVs are generated sample data. Do not commit real student records, credentials, or `.streamlit/secrets.toml`.

1. Sign in to GitHub and create an **empty** repository named `scholarview-academic-analytics`. Choose repository visibility deliberately; do not make real or confidential student data public.
2. Open PowerShell in this project folder and run the following commands. They initialize Git **inside this project folder**, exclude the existing `venv`, and stage only the dashboard, its requirements, its README, and the sample dataset it loads:

   ```powershell
   Set-Location "$HOME\Desktop\academic-performance-analytics\academic-performance-analytics"
   git init -b main
   git add .gitignore README.md app.py requirements.txt data/cleaned_student_data.csv
   git status --short
   git commit -m "Prepare ScholarView for deployment"
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/scholarview-academic-analytics.git
   git push -u origin main
   ```

   Replace `YOUR_GITHUB_USERNAME` with your GitHub username. Review `git status --short` before committing and make sure no real student data or secrets are listed. Git may ask you to authenticate using your normal GitHub sign-in flow; never put a password or access token into the repository.
3. Sign in at [share.streamlit.io](https://share.streamlit.io/), select **Create app**, choose the GitHub repository, branch `main`, and app file `app.py`, then deploy.
4. When deployment finishes, copy the Streamlit app URL and send it to your friend. The app must remain deployed for them to access it.

The GitHub repository URL and the deployed Streamlit app URL are different. Streamlit Cloud needs access to the selected GitHub repository to build and run the app.

## Dashboard features

- Cohort filters for performance band, support status, focus subject, attendance, and student ID.
- KPI cards for cohort size, average score, at-risk students, and attendance.
- Interactive subject-performance, performance-mix, attendance, and learning-gap charts.
- Searchable student records with CSV export.
- Individual student profiles with subject strengths and engagement measures.
- CSV upload for analyzing another cohort.

## CSV format

The uploaded CSV must include these columns:

```text
Student_ID, Attendance_Percent, Study_Hours_Per_Week,
Subject_Math, Subject_Python, Subject_DBMS, Subject_AI
```

Attendance and subject scores must be between 0 and 100. Study hours cannot be negative. Assignment, internal, participation, and previous-semester scores are optional; when supplied, they are shown in the student profile.

The dashboard derives each student's overall average from the four subject scores. It marks students as **At Risk** when their average is below 60. Performance bands are **High** (75 and above), **Medium** (50 to below 75), and **Needs Improvement** (below 50).

## Project structure

```text
app.py                  Streamlit dashboard
data/                   Sample, cleaned, and analyzed student datasets
src/                    Data generation, cleaning, analysis, and ML scripts
outputs/                Saved analysis visualizations
requirements.txt        Dashboard dependencies
```