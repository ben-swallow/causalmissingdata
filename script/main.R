library(tidyverse)
library(parallel)
library(foreach)
library(iterators)
library(doParallel)

# PARAMETERS
# K: Number of visits minus one
# rhos: Parameters for confounding strength (5 scenarios)
# betas: Parameters for the causal effect of interest
# gammas: Parameters for treatment allocation
# thetas: Parameters for the confounding mechanism

setwd("C:/Users/the_o/Desktop/Dissertation/SynthesisationRepo/eave_ii_simulated_data/")

# Load demographics table
demographics <- read.csv("data/multimorbidity.csv", stringsAsFactors = TRUE)
demographics$SCSIMD5 <- as.factor(demographics$SCSIMD5)
demographics$NumComorbidities <- as.factor(demographics$NumComorbidities)
demographics <- demographics[!is.na(demographics$SCSIMD5), ]

levels(demographics$AgeGroup) <- gsub("\\+", "more", gsub("-", "to", levels(demographics$AgeGroup)))

K <- 2 # Number of visits minus one

# Parameter determining the strength of confounding (five scenarios)
rhos <- c(-0.1, -0.3, -0.5, -0.7, -0.9)

# Parameters for causal quantity of interest
betas <- list()
betas[[1]] <- c(-3.5, -0.5)
betas[[2]] <- c(-3.5, -0.5, -0.5)
betas[[3]] <- c(-3.5, 0, -0.5, -0.5)

# Parameters for allocation of treatment to individuals
gammas <- list()
gammas[[1]] <- c(
  -1.5,
  -0.05,
  rep(0.1, nlevels(demographics$AgeGroup)-1),
  rep(-0.05, nlevels(demographics$SCSIMD5)-1),
  rep(0.1, nlevels(demographics$NumComorbidities)-1)
)
gammas[[2]] <- c(
  -1.5,
  -0.05,
  rep(0.1, nlevels(demographics$AgeGroup)-1),
  rep(-0.05, nlevels(demographics$SCSIMD5)-1),
  rep(0.1, nlevels(demographics$NumComorbidities)-1),
  -0.5
)
gammas[[3]] <- c(
  -1.5,
  -0.05,
  rep(0.1, nlevels(demographics$AgeGroup)-1),
  rep(-0.05, nlevels(demographics$SCSIMD5)-1),
  rep(0.1, nlevels(demographics$NumComorbidities)-1),
  0, -0.5
)

# Parameters for confounding mechanism
thetas <- c(
  1,
  rep(2, nlevels(demographics$AgeGroup)-1),
  rep(1, nlevels(demographics$SCSIMD5)-1),
  rep(2, nlevels(demographics$NumComorbidities)-1)
)

# Possible values of tretment allocation vector
a_k_values <- c(
#  "", 
  "0", "1", 
  "00", "01", "10", "11", 
  "000", "001", "010", "011", "100", "101", "110", "111" #,
)

source("script/aux_functions.R")

for (l in 1:length(rhos)) {
  cat("rho = ", rhos[l], "\n")
  rho <- rep(rhos[l], K+1)
  source("script/estimate_cdf.R")
  source("script/simulate_data.R")
  write_csv(as.data.frame(b), paste0("simulations/", l, "/confounders.csv"))
  write_csv(as.data.frame(a), paste0("simulations/", l, "/treatment.csv"))
  write_csv(as.data.frame(y), paste0("simulations/", l, "/outcome.csv"))

  # Combine confounders, treatments, and outcomes into a single data frame
  combined_data <- cbind(as.data.frame(b), as.data.frame(a), as.data.frame(y))

  # Write the combined data to a single CSV file
  write_csv(combined_data, paste0("simulations/", l, "/combined_data.csv"))
}

