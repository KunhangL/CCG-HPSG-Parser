# C&C NLP tools
# Copyright (c) Universities of Edinburgh, Oxford and Sydney
# Copyright (c) James R. Curran
#
# This software is covered by a non-commercial use licence.
# See LICENCE.txt for the full text of the licence.
#
# If LICENCE.txt is not included in this distribution
# please email candc@it.usyd.edu.au to obtain a copy.

source src/scripts/ccg/common

MODEL=$WORK/model_derivs
LOG=$MODEL/log
FORESTS=/tmp/forests.derivs

echo "creating forest files in $FORESTS" | tee -a $LOG

mpiexec -wdir $BASE -n $NNODES $BIN/forests --nsents 39604 \
  --super $SUPER --data $WORK --forests $FORESTS --parser $MODEL \
  --int-betas '0.1' --int-dict_cutoffs '20' \
  2>&1 | tee -a $LOG

echo "creating weights file" | tee -a $LOG

mpiexec -wdir $BASE -n $NNODES $BIN/tree_gis $MODEL/model.config \
  2>&1 | tee -a $LOG
