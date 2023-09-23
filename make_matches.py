import numpy as np
import pandas as pd
import argparse 
from tqdm import tqdm
from pathlib import Path

def split_has_pref(mentee_arr):
    # split into mentees with and without preferences
    mentee_wo_pref_arr = []
    mentee_w_pref_arr = []
    for mentee_info in mentee_arr:
        if all(pref=='' for pref in mentee_info[1:]):
            mentee_wo_pref_arr.append(mentee_info)
        else:
            mentee_w_pref_arr.append(mentee_info)
    return np.array(mentee_w_pref_arr), np.array(mentee_wo_pref_arr)

def get_mentees(mentee_file):
    # read in mentee file
    # mentee file should have header: |Name|Program|1|2|3|
    mentee_df = pd.read_excel(mentee_file, sheet_name="Match_Input")
    if list(mentee_df.columns) != ['Name', 'Program', 1, 2, 3]:
        raise ValueError(f"Column names of mentee file should be: ['Name', 'Program', 1, 2, 3]. \
                         Supplied file has columns {list(mentee_df.columns)}.")
    mentee_df = mentee_df.fillna('')
    
    # separate into MS & PhD mentees, then convert to dictionaries
    keep_cols = ['Name', 1, 2, 3]
    mentee_ms = mentee_df[mentee_df['Program'] == 'MS'][keep_cols].to_numpy()
    mentee_phd = mentee_df[mentee_df['Program'] == 'PhD'][keep_cols].to_numpy()

    return mentee_ms, mentee_phd

def get_mentors(mentor_file):
    # read in mentor file
    # mentor file should have header: |Name|Program|Capacity|
    mentor_df = pd.read_excel(mentor_file, sheet_name="Match_Input")
    if list(mentor_df.columns) != ['Name', 'Program', 'Capacity']:
        raise ValueError(f"Column names of mentor file should be: ['Name', 'Program', 'Capacity']. Supplied file has columns {list(mentor_df.columns)}.")
    mentor_df.set_index('Name', inplace=True)
    
    # separate into MS & PhD mentors, then convert to dictionaries
    mentor_ms_df = mentor_df[mentor_df['Program'] == 'MS']
    mentor_phd_df = mentor_df[mentor_df['Program'] == 'PhD']
    mentor_ms_dict = mentor_ms_df['Capacity'].to_dict()
    mentor_phd_dict = mentor_phd_df['Capacity'].to_dict()

    return mentor_ms_dict, mentor_phd_dict

# update match dictionary and mentor capacity dictionary
def make_match(mentee, mentor, match_arr, rank, mentor_rem_dict):
    match_arr.append([mentee, mentor, rank])
    mentor_rem_dict[mentor] -= 1
    if mentor_rem_dict[mentor] == 0:
        mentor_rem_dict.pop(mentor)
    return match_arr

# make matches for all mentees
def make_all_matches(mentee_arr, mentor_rem_dict, match_arr, ranks, score):
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
        match_arr = make_match(mentee, mentor, match_arr, min(ranks), mentor_rem_dict)
        matched_wop.append(i)

    mentee_wp_rem_arr = np.copy(mentee_wp_arr)
    mentee_wop_rem_arr = np.copy(mentee_wop_arr)
    mentee_wp_rem_arr = np.delete(mentee_wp_rem_arr, matched_wp, 0)
    mentee_wop_rem_arr = np.delete(mentee_wop_rem_arr, matched_wop, 0)
    mentee_rem_arr = np.vstack([mentee_wp_rem_arr, mentee_wop_rem_arr])

    return score, match_arr, mentee_rem_arr

def print_summary(best_match_df, ranks):
    summary_df = best_match_df.value_counts('Rank').to_frame().reset_index().rename(columns={0: 'Num Mentees'})
    names = ['First Choice', 'Second Choice', 'Third Choice', 'Unranked']
    rank_to_name = {str(r):n for (r, n) in zip(ranks, names)}
    summary_df = summary_df.replace({'Rank': rank_to_name}).sort_values(by='Rank')
    
    print(summary_df)

if __name__ == "__main__":
    seed = 42
    np.random.seed(seed)

    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default='data')
    parser.add_argument("--mentee-file", type=str, default='mentees.xlsx')
    parser.add_argument("--mentor-file", type=str, default='mentors.xlsx')
    parser.add_argument("--match-file", type=str, default='matches.xlsx')
    parser.add_argument("--ranks", nargs="+", type=int, default=[0, 2, 5, 11])
    parser.add_argument("--n-iter", type=int, default=int(1e5))
    args = parser.parse_args()

    # read in mentor and mentee data
    data_dir = Path(args.data_dir)
    ranks = np.sort(np.array(args.ranks))
    mentee_ms_arr, mentee_phd_arr = get_mentees(data_dir / args.mentee_file)
    mentor_ms_dict, mentor_phd_dict = get_mentors(data_dir / args.mentor_file)
    print(f"MS mentee count: {len(mentee_ms_arr)}")
    print(f"MS mentor count: {len(mentor_ms_dict)}")
    print(f"PhD mentee count: {len(mentee_phd_arr)}")
    print(f"PhD mentor count: {len(mentor_phd_dict)}")

    # iterate through many possible matchings to find approximate best (highest scoring)
    print("Finding approximate best matching...")
    for iter in tqdm(range(args.n_iter)):
        start_score = 0
        match_arr = []
        mentor_ms_rem_dict = mentor_ms_dict.copy()
        mentor_phd_rem_dict = mentor_phd_dict.copy()

        # make MS mentee matches (first for those with preferences)
        score, match_arr, mentee_rem_arr = make_all_matches(mentee_ms_arr, mentor_ms_rem_dict, match_arr, ranks, start_score)

        # make PhD mentee matches and matches for leftover MS mentees (first for those with preferences)
        mentee_rem_arr = np.vstack([mentee_rem_arr, mentee_phd_arr])
        score, match_arr, mentee_rem_arr = make_all_matches(mentee_rem_arr, mentor_phd_rem_dict, match_arr, ranks, score)

        if iter == 0 or (score < best_score):
            best_score = score
            best_match_arr = np.copy(match_arr)
            best_rem_arr = np.copy(mentee_rem_arr)

    print("Done!")

    if len(mentee_rem_arr) > 0:
        print('The following mentees were unmatched due to insufficient mentor capacity:')
        print(mentee_rem_arr)

    best_match_df = pd.DataFrame(best_match_arr, columns=['Mentee_Name', 'Mentor_Name', 'Rank'])
    print_summary(best_match_df, ranks)

    print(f"Saving matches to {data_dir / args.match_file}")
    best_match_df.to_excel(data_dir / args.match_file, index=False)
