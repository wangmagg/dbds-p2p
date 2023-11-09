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
__```make_matches.py```__: Implementation and execution of the matching algorithm (see details on the algorithm in _Explanation of the Matching "Algorithm"_). <br />
__```compose_emails.py```__: Writes emails to mentors with information on their mentees. Formatting is based on the files in the ```email_inputs``` folder. <br />
__```email_inputs```__: <br />
|__ ```template.txt```: Template email to mentors. Gets filled in for each mentor-mentee pairing by the ```compose_emails.py``` script. <br />
|__ ```dates.csv```: Contains two deadline dates: (1) Deadline for reaching out to mentees. (2) Official DBDS application deadline. These dates are inserted in the email to mentors.

## Explanation of the Matching "Algorithm"

## Usage
__Formatting the Inputs__ 

__Running the Matching__

__Composing the Emails__



