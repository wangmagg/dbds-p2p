import pandas as pd
from tqdm import tqdm
from argparse import ArgumentParser
from pathlib import Path

def load_data(input_dir, output_dir, mentee_file, mentor_file):
    """Load mentee, mentor, and match dataframes.

    Parameters:
        input_dir (str): Input directory containing mentee and mentor spreadsheets.
        output_dir (str): Output directory with match file.
        mentee_file (str): Name of mentee spreadsheet file.
        mentor_file (str): Name of mentor spreadsheet file.

    Returns:
        mentee_df (pd.DataFrame): Mentee spreadsheet as dataframe.
        mentor_df (pd.DataFrame): Mentor spreadsheet as dataframe.
        match_df (pd.DataFrame): Match spreadsheet as dataframe.
    """
    # Load mentees
    # Since some mentees submitted multiple times, get their most recent submission only
    mentee_df = pd.read_excel(input_dir / mentee_file, sheet_name = 'Form Responses 1').rename(columns={'Email address': 'Mentee_Email'})
    mentee_df = mentee_df.groupby('Mentee_Email').apply(
        lambda group: group[group['Timestamp'] == group['Timestamp'].max()])
    
    # Load mentors
    mentor_df = pd.read_excel(input_dir / mentor_file, sheet_name = 'Form Responses 1').rename(columns={'Email Address': 'Mentor_Email'})
    
    # Load matches
    match_df = pd.read_excel(output_dir / 'matches.xlsx')

    return mentee_df, mentor_df, match_df

def merge_mentors_mentees_matches(mentee_df, mentor_df, match_df):
    """Merge mentee, mentor, and match dataframes.

    Parameters:
        mentee_df (pd.DataFrame): Mentee spreadsheet as dataframe.
        mentor_df (pd.DataFrame): Mentor spreadsheet as dataframe.
        match_df (pd.DataFrame): Match spreadsheet as dataframe.

    Returns:
        match_mentee_info_df (pd.DataFrame): Match spreadsheet merged with mentee spreadsheet.
        match_full_info_df (pd.DataFrame): Match spreadsheet merged with mentee and mentor spreadsheets.
    """
    # Merge match and mentee dataframes
    match_mentee_info_df = pd.merge(match_df, 
                                    mentee_df,
                                    how="left",
                                    left_on="Mentee_Name",
                                    right_on="Full name (First and Last)")
    
    # Merge match, mentee, and mentor dataframes
    mentor_df['Name (First Last)'] = mentor_df['First name'] + ' ' + mentor_df['Last name']
    match_mentor_mentee_info_df = pd.merge(match_mentee_info_df,
                                           mentor_df,
                                           how="left",
                                           left_on="Mentor_Name",
                                           right_on="Name (First Last)")

    return match_mentor_mentee_info_df

def compose_email(match_info: pd.Series, 
                  template: str, 
                  dates: pd.DataFrame,
                  email_output_dir: Path) -> None:
    """
    Compose email for a mentor-mentee pair.

    Parameters:
        match_info (pd.Series): Series containing mentor and mentee information.
        template (str): Email template.
        email_output_dir (Path): Directory to save emails to.
    """

    mentor_name = match_info["Mentor_Name"]
    mentee_name = match_info["Mentee_Name"]

    # Fill in template with mentor and mentee information
    template_filled = template.format(
    outreach_deadline=dates['outreach_deadline'][0],
    submission_deadline=dates['submission_deadline'][0],
    mentor_name=mentor_name.split(' ')[0],
    mentor_email=match_info["Mentor_Email"],
    mentee_name=mentee_name,
    mentee_email=match_info["Mentee_Email"],
    program=match_info["I am planning to apply to the DBDS"],
    major=match_info["Current or most recent major"],
    university=match_info["Current or most recent institution  "],
    grad_year=match_info["Expected or most recent year of graduation"],
    research_interests=match_info["My research interests include the following:"],
    how_contribute_diversity=match_info["The DBDS Peer-to-Peer mentoring programs aims to assist applicants who identify as part of a group that has been historically underrepresented in STEM,  including (but not limited to) those from underrepresented backgrounds, such as underrepresented racial and ethnic groups, persons with disabilities and those from disadvantaged backgrounds. How do you as an individual contribute to diversity in STEM? (4-5 sentences)"],
    sop_link=match_info["Upload a PDF of your statement of purpose (Lastname_Firstname_SOP)"])

    # Save email to file
    with open(email_output_dir/ f'{mentor_name}-{mentee_name}.txt', 'w') as f:
        f.write(template_filled)

def main(args: ArgumentParser) -> None:
    # Read in mentor, mentee, and match files
    mentee_df, mentor_df, match_df = load_data(Path(args.input_dir), 
                                               Path(args.output_dir), 
                                               args.mentee_file, 
                                               args.mentor_file)

    # Merge match, mentee, and mentor dataframes
    match_mentor_mentee_info_df = merge_mentors_mentees_matches(mentee_df, mentor_df, match_df)
    
    # Read in email template and dates
    with open("email_inputs/template.txt", 'r') as f:
        template = f.read()
    dates = pd.read_csv("email_inputs/dates.csv")
    
    # Create directory to store emails
    email_subdir = Path(args.output_dir) / "emails"
    if not email_subdir.exists():
        email_subdir.mkdir()

    # Write emails for each mentor-mentee pair
    print("Composing emails...")
    match_mentor_mentee_info_df.apply(lambda x: compose_email(x, template, dates, email_subdir), axis=1)
    print(f"Done! Emails saved to {args.output_dir}/emails/*.")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input-dir", type=str, default='sample_data', help="input directory with mentee and mentor spreadsheet files")
    parser.add_argument("--output-dir", type=str, default='outputs', help="output directory for match file and emails")
    parser.add_argument("--mentee-file", type=str, default='sample_mentees.xlsx', help="name of mentee spreadsheet file")
    parser.add_argument("--mentor-file", type=str, default='sample_mentors.xlsx', help="name of mentor spreadsheet file")
    args = parser.parse_args()

    main(args)




