# scenario.R

ESampleSize <- list(
  SMALL = 1000,
  MEDIUM = 5000#,
  #LARGE = 10000
)

ERho <- list(
  WEAK_NEG = -0.1,
  MILD_NEG = -0.4,
  MODERATE_NEG = -0.7#,
  #STRONG_NEG = -0.7,
  #VERY_STRONG_NEG = -0.9
)

EEffectSize <- list(
  SMALL = 0.5
)

EMissingnessMechanism <- list(
  MAR = "MAR",
  MARY = "MARY",
  MCAR = "MCAR",
  MNAR = "MNAR"
)

ETargetVariable <- list(
  A0 = "A0",
  A1 = "A1",
  A2 = "A2",
  Y1 = "Y1",
  Y2 = "Y2",
  Y3 = "Y3"
)

EPredictorVariable <- list(
  A0 = "A0",
  A1 = "A1",
  Y1 = "Y1",
  Y2 = "Y2", 
  NumComorbidities = "NumComorbidities",
  AgeGroup = "AgeGroup",
  SCSIMD5 = "SCSIMD5"
)

EMethod <- list(
  COMPLETE_CASE = "complete_case"
)

EMissingRate <- list(
  LOW = 0.20,
  #MEDIUM = 0.20,
  HIGH = 0.50
)

Scenario <- function(mechanism, missing_rate, method, rho, sample_size, 
                     target_vars = NULL, predictors = NULL) {
  scenario <- structure(list(
    # scenario parameters
    mechanism = mechanism,
    missing_rate = missing_rate,
    method = method,
    rho = rho,
    sample_size = sample_size,
    target_vars = target_vars,
    predictors = predictors,
    metrics = NULL
  ), class = "Scenario")

  return(scenario)
}

scenario_to_df <- function(scenario) {
  if (is.null(scenario$metrics)) {
    stop("No metrics found in scenario object.")
  }
  scenario_df <- data.frame(
    mechanism = scenario$mechanism,
    missing_rate = scenario$missing_rate,
    rho = scenario$rho,
    sample_size = scenario$sample_size,
    target_vars = paste(unlist(scenario$target_vars), collapse = ","),
    predictors = paste(unlist(scenario$predictors), collapse = ","),
    stringsAsFactors = FALSE
  )
  # Repeat scenario_df for each row in metrics
  scenario_df_rep <- scenario_df[rep(1, nrow(scenario$metrics)), ]
  # Combine
  combined <- cbind(scenario_df_rep, scenario$metrics)
  # Move 'method' to the first column if it exists
  if ("method" %in% colnames(combined)) {
    combined <- combined[, c("method", setdiff(colnames(combined), "method"))]
  }
  return(combined)
}