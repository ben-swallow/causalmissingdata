library(tidyverse)
library(parallel)
library(foreach)
library(iterators)
library(doParallel)
library(sandwich)

#setwd("C:/Users/the_o/Desktop/Dissertation/SynthesisationRepo/eave_ii_simulated_data")


model_data <- function(df, rho)
{
    model.outcome.unweighted <- list()
    propensity_score_violations <- list()
    
    # Extract data from the df passed from main.R
    n_confounders <- 4  # Sex, AgeGroup, SCSIMD5, NumComorbidities
    n_treatments <- 3   # A0, A1, A2

    b <- df[, 1:n_confounders] |>
      as.data.frame()
    
    # Assign proper column names since they were lost in Python conversion
    colnames(b) <- c("Sex", "AgeGroup", "SCSIMD5", "NumComorbidities")
    
    # Convert to factors
    b <- b |> mutate_all(factor)
    
    a <- df[, (n_confounders + 1):(n_confounders + n_treatments)] |> 
      as.data.frame() |> 
      as.matrix()
    y <- df[, (n_confounders + n_treatments + 1):ncol(df)] |> 
      as.data.frame() |> 
      as.matrix()
      
    b_coded <- cbind(
      encode_binary(b$Sex, name = "Sex"),
      encode_ordinal(b$AgeGroup, name = "AgeGroup"),
      encode_ordinal(b$SCSIMD5, name = "SCSIMD5"),
      encode_ordinal(b$NumComorbidities, name = "NumComorbidities")
    )

    failure_times <- rowSums(y)
  for (k in 1:(K+1)) {
    model.outcome.unweighted[[k]] <- glm(
      as.factor(y[,k+1]==0) ~ a[,1:k], 
      family = binomial, 
      subset = which(failure_times>=k)
    ) 
  }
  
  N <- nrow(b)
  w <- matrix(1, N, K+1)
  model.outcome.weighted <- list()
  for (k in 1:(K+1)) {
    if (k == 1) {
      fit.numer <- glm(a[, 1] ~ 1, family = binomial)
      fit.denom <- glm(a[, 1] ~ b_coded, family = binomial)
    } else {
      fit.numer <- glm(a[, k] ~ a[,(1:(k-1))], family = binomial, subset = which(failure_times>=k))
      fit.denom <- glm(a[, k] ~ a[,(1:(k-1))] + b_coded, family = binomial, subset = which(failure_times>=k))
    }

    denominator = fitted(fit.denom)
    numerator = fitted(fit.numer)
    extreme_count <- sum(denominator < 0.05 | denominator > 0.95)
        violation_prop <- extreme_count / length(denominator)

    propensity_score_violations[[k]] <- violation_prop

    phat.denom <- a[failure_times>=k, k] * denominator + (1-a[failure_times>=k, k]) * (1- denominator)
    phat.numer <- a[failure_times>=k, k] * numerator + (1-a[failure_times>=k, k]) * (1- numerator)
    if (k == 1) {
      w[, k] <- phat.numer / phat.denom
    } else {
      w[failure_times>=k, k] <- w[failure_times>=k,k-1] * phat.numer / phat.denom
    }
    model.outcome.weighted[[k]] <- glm(
      as.factor(y[,k+1]==0) ~ a[,1:k], 
      family = binomial, 
      weights = w[, k], 
      subset = which(failure_times>=k)
    )
  }
  
    robust_ses <- list()
    for (k in 1:(K+1)) {
        robust_vcov <- vcovHC(model.outcome.weighted[[k]], type="HC3")
        robust_ses[[k]] <- sqrt(diag(robust_vcov))
    }
    
    # Create param.estimates with robust SEs
    param.estimates <- do.call(rbind, lapply(1:3, 
        function(i) cbind(
            betas[[i]],
            coefficients(summary(model.outcome.unweighted[[i]]))[,1:2],
            coefficients(summary(model.outcome.weighted[[i]]))[,1],
            robust_ses[[i]],
            propensity_score_violations[[i]]
        ) |> round(4)
    ))

    colnames(param.estimates)[1] <- "True value"

    return(list(
        param_estimates = param.estimates,
        violations = propensity_score_violations
    ))
}