# Stanford DBDS Peer-to-Peer Mentor<>Mentee Matching
Makes approximately optimal mentor-mentee matchings using a non-exhaustive, enumerative search strategy. 

## Setup
__Installation__ <br />
To download the code, run the following commands <br />
```
git clone https://github.com/wangmagg/dbds-p2p.git
cd dbds-p2p
```
__Conda Environment__ <br />
To create and activate the conda environment, run the following commands from the dbds-p2p directory <br />
```
conda env create -f environment.yml
conda activate dbds-p2p-env
```
This will ensure that the necessary package dependencies are installed.

## File Descriptions
```
├── README.md 
├── email_inputs
│   ├── dates.csv
│   └── template.txt
├── emails.py
├── environment.yml
├── matches.py
├── p2p.sh
├── requirements.txt
└── sample_data
    ├── sample_mentees.xlsx
    └── sample_mentors.xlsx
```

## Explanation of the Matching "Algorithm"
This is a naive, brute force matching algorithm, but it works reasonably well (I think; someone smarter than me can try coming up with one that's more clever). 

### Measuring the "goodness" of a particular matching
At initialization, we specify a score for each possible type of match that can be formed: mentee with first choice mentor, mentee with second choice mentor, mentee with third choice mentor, mentee with an unranked mentor. Lower scores are considered better. For example, we might assign a score of 0 if a mentee is matched with their first choice, a score of 2 if they are matched with their second choice, a score of 5 if they're matched with their third choice, and a score of 20 if they are matched with an unranked mentor (this is the default scoring scheme in the code). These scores can be adjusted, depending on which kinds of matches you want to prioritize. The overall score for a particular matching is the sum of scores across all matches. 

### Producing a matching
The general procedure for making a single match between a mentee and a mentor is as follows: 
* If the mentee has specified one or more preferred mentors, randomly choose one of these preferred mentors. If that mentor has any capacity remaining, make a match between the mentee and the mentor, then decrement the mentor's remaining capacity. If the mentor does not have any capacity remaining, randomly choose _any_ of the mentors with remaining capacity (which may or may not be one of the mentee's preferred mentors), and make a match.
* If the mentee has not specified any preferred mentors, randomly choose any mentor with remaining capacity, and make a match.

To make a matching between all mentees and mentors, we do the following:
* __Make matches between MS mentors and MS mentees__. Ideally, we do not want MS mentors to be matched with PhD mentees. Assuming there are more mentees than mentors (which has typically been the case), if we match all the MS mentors first, then we do not need to be worried about the issue of an _MS mentor <> PhD mentee_ pairing. We first split the MS mentees into two categories: those with mentor preferences and those without. Starting with the mentees with preferences, we shuffle the order of the mentees, then pair them off sequentially, using the single match procedure described above. We then shuffle the order of the mentees without preferences and pair them off. If at any point we run out of MS mentors, we stop and move on to the step below.

* __Make matches between the PhD mentors and the PhD mentees, as well as any MS mentees who did not get matched in the previous step__. Using the same procedure as above, we make matches between all remaining mentees and the PhD mentors. 

__Repeatedly producing possible matchings and picking the final one__
We repeat the above procedure many times to produce many candidate matchings. We calculate the score for each matching, then keep the one with the lowest score. This is the final matching.


## Usage
### Inputs
In order to run the code, the inputs need to be formatted in a very specific way. 

In the ```sample_data``` folder, you will find examples of how the inputs to the matching algorithm should be formatted. You will need to provide one Excel file containing mentee information and one containing mentor information. 

__Mentor file formatting__
The mentor file should contain two sheets: "Form Responses 1" and "Match_Input". "Form Responses 1" is the data that you will get from the Google form.

"Match_Input" is an additional sheet that you will need to construct manually. This sheet should have 3 columns, "Name", "Capacity", and "Program", in that order. "Name" should contain the first and last name of the mentor. "Capacity" should contain their specified mentee capacity. "Program" should contain which degree program they are a part of, either "MS" or "PhD". 

__Mentee file formatting__
The mentor file should contain two sheets: "Form Responses 1" and "Match_Input". "Form Responses 1" is the data that you will get from the Google form.

"Match_Input" is an additional sheet that you will need to construct manually. This sheet should have 4 columns, "Name", "Program", "1", "2", and "3", in that order. "Name" should contain the first and last name of the mentee. "Program" should contain which degree program they are applying to, either "MS" or "PhD". "1", "2", and "3" should contain the first and last names of their first choice, second choice, and third choice mentors, respectively (if specified). If any of the first, second, or third choice mentors are not specified by the mentee, then the cell should be left blank.

In the ```email_inputs``` folder, you will find the template for writing emails to the mentors and a ```dates.csv``` file containing 2 key dates: the deadline for mentors to reach out to their mentees, and the deadline for mentees to submit their DBDS application. You will need to update these dates for the current application cycle.

### Running the Matching
To run the matching algorithm, run the ```matches.py`` Python script:
```
python3 matches.py \
    --input-dir [NAME OF INPUT DIRECTORY CONTAINING MENTOR AND MENTEE FILES] \
    --output-dir [NAME OF OUTPUT DIRECTORY] \
    --mentee-file [NAME OF MENTEE FILE] \
    --mentor-file [NAME OF MENTOR FILE] \
    --ranks [SCORES FOR 1ST, 2ND, 3RD, AND UNRANKED MENTORS] \
    --n-iter [NUMBER OF CANDIDATE MATCHINGS TO GENERATE]
```
This will create a file called ```matches.xlsx``` in the specified output directory containing all mentor <> mentee matches.

### Composing the Emails
To make it easier to send out emails to the mentors with their mentee information, we provide a Python script that populates an email template. To generate these emails, run the ```emails.py``` script:

```
python3 emails.py \
    --input-dir [NAME OF INPUT DIRECTORY CONTAINING DATES FILE AND EMAIL TEMPLATE] \
    --output-dir [NAME OF OUTPUT DIRECTORY] \
    --mentee-file [NAME OF MENTEE FILE] \
    --mentor-file [NAME OF MENTOR FILE] \
```
Make sure the dates file has updated dates!

This will create a folder called ```emails``` in the specified output directory with filenames ```[MENTOR FIRST LAST]_[MENTEE FIRST LAST].txt```. 

For added convenience, you can also combine the matching and email composition by running ```p2p.sh```.


