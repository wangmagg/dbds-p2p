import numpy as np
import pandas as pd
from argparse import ArgumentParser
from tqdm import tqdm
from pathlib import Path
from typing import List

def get_mentees(mentee_file: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Gets mentee information (name and ranked mentor preferences) from mentee file.

    Parameters:
        mentee_file (str): filename of mentee spreadsheet file, e.g. mentees.xlsx
    Returns:
        mentee_ms (np.ndarray): array of MS mentee information
        mentee_phd (np.ndarray): array of PhD mentee information
    """
    # read in mentee file
    # mentee file should contain columns: |Name|Program|1|2|3|
    mentee_df = pd.read_excel(mentee_file, sheet_name="Match_Input")
    if not set(['Name', 'Program', 1, 2, 3]).issubset(set(mentee_df.columns)):
        raise ValueError(f"Column names of mentee file should be: ['Name', 'Program', 1, 2, 3]. \
                         Supplied file has columns {list(mentee_df.columns)}.")
    mentee_df = mentee_df.fillna('')
    
    # separate into MS & PhD mentees, then convert to dictionaries
    keep_cols = ['Name', 1, 2, 3]
    mentee_df['Program'] = mentee_df['Program'].apply(lambda x: x.strip()) # strip whitespace from program names
    mentee_ms = mentee_df[mentee_df['Program'] == 'MS'][keep_cols].to_numpy()
    mentee_phd = mentee_df[mentee_df['Program'] == 'PhD'][keep_cols].to_numpy()

    print("Mentee counts:")
    print("   MS:", len(mentee_ms))
    print("   PhD:", len(mentee_phd))
    print("   Total:", len(mentee_ms) + len(mentee_phd))

    return mentee_ms, mentee_phd

def get_mentors(mentor_file: str) -> tuple[dict, dict]:
    """
    Gets mentor information (name and capacity) from mentor file.

    Parameters:
        mentor_file (str): filename of mentor spreadsheet file, e.g. mentors.xlsx
    Returns:
        mentor_ms_dict (dict): dictionary of MS mentor capacities
        mentor_phd_dict (dict): dictionary of PhD mentor capacities
    """
    # read in mentor file
    # mentor file should contain columns: |Name|Program|Capacity|
    mentor_df = pd.read_excel(mentor_file, sheet_name="Match_Input")
    if not set(['Name', 'Program', 'Capacity']).issubset(set(mentor_df.columns)):
        raise ValueError(f"Column names of mentor file should be: ['Name', 'Program', 'Capacity']. \
                          Supplied file has columns {list(mentor_df.columns)}.")
    mentor_df.set_index('Name', inplace=True)
    
    # separate into MS & PhD mentors, then convert to dictionaries
    mentor_ms_df = mentor_df[mentor_df['Program'] == 'MS']
    mentor_phd_df = mentor_df[mentor_df['Program'] == 'PhD']
    mentor_ms_dict = mentor_ms_df['Capacity'].astype(int).to_dict()
    mentor_phd_dict = mentor_phd_df['Capacity'].astype(int).to_dict()

    print("Mentor counts:")
    print("   MS:", len(mentor_ms_dict))
    print("   PhD:", len(mentor_phd_dict))
    print("   Total:", len(mentor_ms_dict) + len(mentor_phd_dict))
    print(f"   Total capacity: {sum(mentor_ms_dict.values()) + sum(mentor_phd_dict.values())}")


    return mentor_ms_dict, mentor_phd_dict

def split_has_pref(mentee_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Splits mentees into those with preferences and those without.

    Parameters:
        mentee_arr (np.ndarray): array of mentee information
    """
    # split into mentees with and without preferences
    mentee_wo_pref_arr = []
    mentee_w_pref_arr = []
    for mentee_info in mentee_arr:
        if all(pref=='' for pref in mentee_info[1:]):
            mentee_wo_pref_arr.append(mentee_info)
        else:
            mentee_w_pref_arr.append(mentee_info)
    return np.array(mentee_w_pref_arr), np.array(mentee_wo_pref_arr)

def make_match(mentee: str, 
               mentor: str, 
               match_arr: List[List], 
               rank: int, 
               mentor_rem_dict: dict) -> List:
    """
    Makes a mentor-mentee match and adds it to the match array.
    Updates the mentor capacity dictionary.

    Parameters:
        mentee (str): mentee name
        mentor (str): mentor name
        match_arr (List[List]): list of matches made so far
        rank (int): rank of mentor for mentee
        mentor_rem_dict (dict): dictionary of remaining mentor capacities

    Returns:
        match_arr (List[List]): updated list of matches made so far
    """
    match_arr.append([mentee, mentor, rank])
    mentor_rem_dict[mentor] -= 1
    if mentor_rem_dict[mentor] == 0:
        mentor_rem_dict.pop(mentor)
    return match_arr

def make_matches(mentee_arr: np.ndarray, 
                 mentor_rem_dict: dict, 
                 match_arr: List[List], 
                 ranks: List[int], 
                 score: int) -> tuple[int, List[List], np.ndarray]:
    
    """
    Makes matches between mentees and mentors with capacity.

    Parameters:
        mentee_arr (np.ndarray): array of mentee information for mentees to be matched
        mentor_rem_dict (dict): dictionary of remaining mentor capacities
        match_arr (List[List]): list of matches made so far
        ranks (List[int]): scores for first, second, third, and unranked choices
        score (int): current score for the matches made

    Returns:
        score (int): updated score for the matches made
        match_arr (List[List]): updated list of matches made so far
        mentee_rem_arr (np.ndarray): array of mentees who were not matched
    """
    # split mentees into those with and without preferences
    mentee_wp_arr, mentee_wop_arr = split_has_pref(mentee_arr)

    # make matches for mentees with preferences
    np.random.shuffle(mentee_wp_arr)
    matched_wp = []
    for i, mentee_info in enumerate(mentee_wp_arr):
        if len(mentor_rem_dict) == 0:
            # if no mentors left, stop
            break
        else: 
            # randomly choose a preferred mentor
            mentee, prefs = mentee_info[0], mentee_info[1:]
            mentor_idx = np.random.choice(np.nonzero(prefs != '')[0])
            mentor, rank = prefs[mentor_idx], ranks[mentor_idx]
            if mentor in mentor_rem_dict:
                # lock in match if preferred mentor has capacity
                match_arr = make_match(mentee, mentor, match_arr, rank, mentor_rem_dict)
                matched_wp.append(i)
                score += rank
            else:
                # if no capacity, choose random mentor
                mentor = np.random.choice(list(mentor_rem_dict.keys()))
                match_arr = make_match(mentee, mentor, match_arr, max(ranks), mentor_rem_dict)
                matched_wp.append(i)
                score += max(ranks)

    # make matches for mentees without preferences
    matched_wop = []
    for i, mentee_info in enumerate(mentee_wop_arr):
        if len(mentor_rem_dict) == 0:
            # if no mentors left, stop
            break
        # since no preference, choose random mentor
        mentor = np.random.choice(list(mentor_rem_dict.keys()))
        mentee, prefs = mentee_info[0], mentee_info[1:]
        match_arr = make_match(mentee, mentor, match_arr, max(ranks), mentor_rem_dict)
        matched_wop.append(i)

    # remove matched mentees from mentee array to get remaining mentees
    mentee_wp_rem_arr = np.copy(mentee_wp_arr)
    mentee_wop_rem_arr = np.copy(mentee_wop_arr)
    mentee_wp_rem_arr = np.delete(mentee_wp_rem_arr, matched_wp, 0)
    mentee_wop_rem_arr = np.delete(mentee_wop_rem_arr, matched_wop, 0)

    # combine remaining mentees with and without preferences
    if len(mentee_wp_rem_arr) == 0:
        mentee_rem_arr = mentee_wop_rem_arr
    elif len(mentee_wop_arr) == 0:
        mentee_rem_arr = mentee_wp_rem_arr
    else:
        mentee_rem_arr = np.vstack([mentee_wp_rem_arr, mentee_wop_rem_arr]) 

    return score, match_arr, mentee_rem_arr

def print_match_summary(best_match_df: pd.DataFrame, 
                        ranks: List[int]) -> None:
    """
    Prints results of matching.

    Parameters:
        best_match_df (pd.DataFrame): dataframe of matches made for the best matching
        ranks (List[int]): scores for first, second, third, and unranked choices
    """
    summary_df = best_match_df.value_counts('Rank').to_frame().reset_index().rename(columns={0: 'Num Mentees'})
    names = ['First Choice', 'Second Choice', 'Third Choice', 'Unranked']
    rank_to_name = {str(r):n for (r, n) in zip(ranks, names)}
    summary_df = summary_df.replace({'Rank': rank_to_name}).sort_values(by='Rank')
    
    print(summary_df)

def main(args: ArgumentParser) -> None:
    """
    Runs mentor-mentee matching algorithm.

    Parameters:
        args (argparse.Namespace): arguments for running matching algorithm
    """
    # set random seed
    np.random.seed(args.seed)

    # read in mentor and mentee data
    input_dir = Path(args.input_dir)
    ranks = np.sort(np.array(args.ranks))
    mentee_ms_arr, mentee_phd_arr = get_mentees(input_dir / args.mentee_file)
    mentor_ms_dict, mentor_phd_dict = get_mentors(input_dir / args.mentor_file)

    # iterate through many possible matchings to find approximate best (highest scoring)
    print("Finding approximate best matching...")
    for iter in tqdm(range(args.n_iter)):
        start_score = 0
        match_arr = []
        mentor_ms_rem_dict = mentor_ms_dict.copy()
        mentor_phd_rem_dict = mentor_phd_dict.copy()

        # make MS mentee matches (first for those with preferences)
        score, match_arr, mentee_rem_arr = make_matches(mentee_ms_arr, mentor_ms_rem_dict, match_arr, ranks, start_score)

        # make PhD mentee matches and matches for leftover MS mentees (first for those with preferences)
        mentee_rem_arr = np.vstack([mentee_rem_arr, mentee_phd_arr])
        score, match_arr, mentee_rem_arr = make_matches(mentee_rem_arr, mentor_phd_rem_dict, match_arr, ranks, score)

        if iter == 0 or (score < best_score):
            best_score = score
            best_match_arr = np.copy(match_arr)
            best_rem_arr = np.copy(mentee_rem_arr)
    print("Done!")

    # Print any mentees that were unmatched
    print('Names of unmatched mentees due to insufficient mentor capacity:', best_rem_arr)

    # Print match results
    best_match_df = pd.DataFrame(best_match_arr, columns=['Mentee_Name', 'Mentor_Name', 'Rank'])
    print_match_summary(best_match_df, ranks)

    # Save matches
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        output_dir.mkdir()
    best_match_df.to_excel(output_dir / 'matches.xlsx', index=False)
    print(f"Matched saved to {output_dir / 'matches.xlsx'}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input-dir", type=str, default='sample_data', help="input directory with mentee and mentor spreadsheet files")
    parser.add_argument("--output-dir", type=str, default='outputs', help="output directory for match file")
    parser.add_argument("--mentee-file", type=str, default='sample_mentees.xlsx', help="name of mentee spreadsheet file")
    parser.add_argument("--mentor-file", type=str, default='sample_mentors.xlsx', help="name of mentor spreadsheet file")
    parser.add_argument("--ranks", nargs="+", type=int, default=[0, 2, 5, 20], help="scores for first, second, third, and unranked choices")
    parser.add_argument("--n-iter", type=int, default=int(1e5), help="number of iterations to run in order to find approximate best matching")
    parser.add_argument("--seed", type=int, default=42, help="random seed for reproducibility")
    args = parser.parse_args()

    main(args)