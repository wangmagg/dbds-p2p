import numpy as np
import pandas as pd
from argparse import ArgumentParser
from pathlib import Path

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--data-dir", type=str, default='data')
    parser.add_argument("--match-file", type=str, default='matches.xlsx')
    parser.add_argument("--mentee-file", type=str, default='mentees.xlsx')
    parser.add_argument("--mentor-file", type=str, default='mentors.xlsx')
    parser.add_argument("--template-file", type=str, default='email_template.txt')
    parser.add_argument("--dates-file", type=str, default='application_dates.csv')
    parser.add_argument("--email-dir", type=str, default='emails')

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    match_df = pd.read_excel(data_dir / args.match_file)
    mentee_df = pd.read_excel(data_dir / args.mentee_file, sheet_name = 'Form Responses 1').rename(columns={'Email address': 'Mentee_Email'})
    mentor_df = pd.read_excel(data_dir / args.mentor_file, sheet_name = 'Form Responses 1').rename(columns={'Email Address': 'Mentor_Email'})

    # Since some mentees submitted multiple times, get their most recent submission only
    mentee_df = mentee_df.groupby('Mentee_Email').apply(
        lambda group: group[group['Timestamp'] == group['Timestamp'].max()])

    # Merge match, mentee, and mentor dataframes
    match_mentee_info_df = pd.merge(match_df, 
                                    mentee_df,
                                    how="left",
                                    left_on="Mentee_Name",
                                    right_on="Full name (First and Last)")
    
    match_full_info_df = pd.merge(match_mentee_info_df,
                                  mentor_df,
                                  how="left",
                                  left_on="Mentor_Name",
                                  right_on="Name (First Last)")
    
    
    with open(args.template_file, 'r') as f:
        template = f.read()
    dates = pd.read_csv(args.dates_file)
    
    email_dir = Path(args.email_dir)
    if not email_dir.exists():
        email_dir.mkdir()

    for _, match_info in match_full_info_df.iterrows():
        mentor_name = match_info["Mentor_Name"]
        mentee_name = match_info["Mentee_Name"]

        template_filled = template.format(
            outreach_deadline=dates['outreach_deadline'][0],
            submission_deadline=dates['submission_deadline'][0],
            mentor_name=mentor_name.split(' ')[0],
            mentor_email=match_info["Mentor_Email"],
            mentee_name=mentee_name,
            mentee_email=match_info["Mentee_Email"],
            program=match_info["I am planning to apply to the BMI"],
            major=match_info["Current or most recent major"],
            university=match_info["Current or most recent institution  "],
            grad_year=match_info["Expected or most recent year of graduation"],
            research_interests=match_info["Research interests include the following:"],
            how_contribute_diversity=match_info["The BMI Peer-to-Peer mentoring programs aims to assist applicants who identify as part of a group that has been historically underrepresented in STEM.  How do you as an individual contribute to diversity in STEM? (4-5 sentences)"],
            sop_link=match_info["Upload a PDF of your statement of purpose (Lastname_Firstname_SOP)"])

        with open(email_dir / f'{mentor_name}-{mentee_name}.txt', 'w') as f:
            f.write(template_filled)






