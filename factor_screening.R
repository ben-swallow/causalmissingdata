source(file.path(pythonPath, "scenario.R"))

create_baseline_scenarios <- function() {
    scenarios <- list()

    # define baseline scenario
    baseline <- Scenario(
        mechanism = EMissingnessMechanism$MAR, 
        missing_rate = EMissingRate$LOW, 
        method = EMethod$COMPLETE_CASE, 
        rho = ERho$WEAK_NEG, 
        sample_size = ESampleSize$MEDIUM, 
        effect_size = EEffectSize$SMALL,
        target_vars = list(ETargetVariable$A2, ETargetVariable$Y2),
        predictors = list(EPredictorVariable$Y1)
    )
    index = 1

    # mehcnism
    scenario_mechanism <- unserialize(serialize(baseline, NULL))
    scenario_mechanism$mechanism <- EMissingnessMechanism$MCAR
    scenarios[[index]] <- scenario_mechanism
    index <- index + 1
    scenario_mechanism$mechanism <- EMissingnessMechanism$MAR
    scenarios[[index]] <- scenario_mechanism
    index <- index + 1
    scenario_mechanism$mechanism <- EMissingnessMechanism$MNAR
    scenarios[[index]] <- scenario_mechanism
    index <- index + 1

    # missing rate
    scenario_missing_rate <- unserialize(serialize(baseline, NULL))
    scenario_missing_rate$missing_rate <- EMissingRate$LOW
    scenarios[[index]] <- scenario_missing_rate
    index <- index + 1
    # scenario_missing_rate$missing_rate <- EMissingRate$MEDIUM
    # scenarios[[index]] <- scenario_missing_rate
    scenario_missing_rate$missing_rate <- EMissingRate$HIGH
    scenarios[[index]] <- scenario_missing_rate
    index <- index + 1

    # rho
    scenario_rho <- unserialize(serialize(baseline, NULL))
    scenario_rho$rho <- ERho$WEAK_NEG
    scenarios[[index]] <- scenario_rho
    index <- index + 1
    scenario_rho$rho <- ERho$MILD_NEG
    scenarios[[index]] <- scenario_rho
    index <- index + 1
    scenario_rho$rho <- ERho$MODERATE_NEG
    scenarios[[index]] <- scenario_rho
    index <- index + 1
    # scenario_rho$rho <- ERho$STRONG_NEG
    # scenarios[[index]] <- scenario_rho
    # scenario_rho$rho <- ERho$VERY_STRONG_NEG
    # scenarios[[index]] <- scenario_rho

    # sample size
    scenario_sample_size <- unserialize(serialize(baseline, NULL))
    scenario_sample_size$sample_size <- ESampleSize$SMALL
    scenarios[[index]] <- scenario_sample_size
    index <- index + 1
    scenario_sample_size$sample_size <- ESampleSize$MEDIUM
    scenarios[[index]] <- scenario_sample_size
    index <- index + 1
    # scenario_sample_size$sample_size <- ESampleSize$LARGE
    # scenarios[[index]] <- scenario_sample_size

    # effect size
    scenario_effect_size <- unserialize(serialize(baseline, NULL))
    scenario_effect_size$effect_size <- EEffectSize$SMALL
    scenarios[[index]] <- scenario_effect_size
    index <- index + 1
    scenario_effect_size$effect_size <- EEffectSize$MEDIUM
    scenarios[[index]] <- scenario_effect_size
    index <- index + 1
    scenario_effect_size$effect_size <- EEffectSize$LARGE
    scenarios[[index]] <- scenario_effect_size
    index <- index + 1

    # scenario_targets_predictors
    # MCAR
    scenario_targets_predictors <- unserialize(serialize(baseline, NULL))
    scenario_targets_predictors$mechanism <- EMissingnessMechanism$MCAR
    scenario_targets_predictors$target_vars <- list(ETargetVariable$Z, ETargetVariable$A1, ETargetVariable$Y2)
    scenario_targets_predictors$predictors <- list()
    scenarios[[index]] <- scenario_targets_predictors
    index <- index + 1

    # MAR monotone
    scenario_targets_predictors <- unserialize(serialize(baseline, NULL))
    scenario_targets_predictors$mechanism <- EMissingnessMechanism$MAR
    scenario_targets_predictors$target_vars <- list(ETargetVariable$A1, ETargetVariable$Y2, ETargetVariable$A2, ETargetVariable$Y3)
    scenario_targets_predictors$predictors <- list(ETargetVariable$Y1)
    scenarios[[index]] <- scenario_targets_predictors
    index <- index + 1

    # MAR intermittent
    scenario_targets_predictors <- unserialize(serialize(baseline, NULL))
    scenario_targets_predictors$mechanism <- EMissingnessMechanism$MAR
    scenario_targets_predictors$target_vars <- list(ETargetVariable$A2, ETargetVariable$Y2)
    scenario_targets_predictors$predictors <- list(ETargetVariable$Y1)
    scenarios[[index]] <- scenario_targets_predictors
    index <- index + 1

    # MNAR
    scenario_targets_predictors <- unserialize(serialize(baseline, NULL))
    scenario_targets_predictors$mechanism <- EMissingnessMechanism$MAR
    scenario_targets_predictors$target_vars <- list(ETargetVariable$A1, ETargetVariable$Y2)
    scenario_targets_predictors$predictors <- list(ETargetVariable$A1, ETargetVariable$Y2)
    scenarios[[index]] <- scenario_targets_predictors
    index <- index + 1

    return (scenarios)
}