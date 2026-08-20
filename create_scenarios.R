source(file.path(pythonPath, "scenario.R"))
mechanism_settings <- list(
  MARY = list(
    list(target_vars = list(ETargetVariable$Y1, ETargetVariable$Y2), predictors = list(EPredictorVariable$NumComorbidities, EPredictorVariable$NumComorbidities))
  ),
  MCAR = list(
    list(target_vars = list(ETargetVariable$A1, ETargetVariable$A2), predictors = list())
  ),
  MAR = list(
    list(target_vars = list(ETargetVariable$A1, ETargetVariable$A2), predictors = list(EPredictorVariable$NumComorbidities, EPredictorVariable$NumComorbidities))
  ),
  MNAR = list(
    list(target_vars = list(ETargetVariable$A1, ETargetVariable$A2), predictors = list(EPredictorVariable$A1, EPredictorVariable$A2))
  )
)

create_full_factorial_scenarios <- function() {
  mechanisms <- names(mechanism_settings)
  missing_rates <- unlist(EMissingRate)
  rhos <- unlist(ERho)
  sample_sizes <- unlist(ESampleSize)

  param_grid <- expand.grid(
    mechanism = mechanisms,
    missing_rate = missing_rates,
    rho = rhos,
    sample_size = sample_sizes,
    stringsAsFactors = FALSE
  )

  scenarios <- list()
  idx <- 1

  for (i in seq_len(nrow(param_grid))) {
    mech <- param_grid$mechanism[i]
    pairs_list <- mechanism_settings[[mech]]
    for (pair in pairs_list) {
      scenario <- Scenario(
        mechanism = param_grid$mechanism[i],
        missing_rate = param_grid$missing_rate[i],
        method = param_grid$method[i],
        rho = param_grid$rho[i],
        sample_size = param_grid$sample_size[i],
        target_vars = pair$target_vars,
        predictors = pair$predictors
      )
      scenarios[[idx]] <- scenario
      idx <- idx + 1
    }
  }
  return(scenarios)
}