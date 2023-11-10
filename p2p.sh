#!/bin/bash

python3 matches.py \
    --input-dir sample_data \
    --output-dir outputs \
    --mentee-file sample_mentees.xlsx \
    --mentor-file sample_mentors.xlsx \
    --ranks 0 2 5 20 \
    --n-iter 100000

python3 emails.py \
    --input-dir sample_data \
    --output-dir outputs \
    --mentee-file sample_mentees.xlsx \
    --mentor-file sample_mentors.xlsx \
