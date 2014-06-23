#!/bin/bash

for CHAPTER in *; do 
    if [ -d ${CHAPTER} ]; then 
        for f in ${CHAPTER}/figures/PDF/*; do 
            if [ -f $f ]; then 
                convert $f ${CHAPTER}/figures/EPS/$(basename $f|sed 's/.pdf$/.eps/'); 
            fi; 
        done; 
    fi; 
done

for i in 5_evaluation/figures/PNG/charts/figures/*pdf; do 
    convert $i 5_evaluation/figures/EPS/charts/figures/$(basename $i|sed 's/.pdf$/.eps/'); 
done
