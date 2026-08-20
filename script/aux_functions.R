encode_binary <- function(x, name = "") {
  factors <- levels(x)
  binary_encoding <- ifelse(x == factors[2], 1, 0)
  binary_encoding <- matrix(binary_encoding, ncol = 1)
  colnames(binary_encoding) <- paste0(name, factors[2])
  return(binary_encoding)
}

encode_ordinal <- function(x, name = "") {
  factors <- levels(x)
  L <- length(factors)
  factors_matrix <- matrix(0, nrow = L, ncol = L-1)
  factors_matrix[lower.tri(factors_matrix)] <- 1
  colnames(factors_matrix) <- paste0(name, "GE", factors[2:L])
  return(factors_matrix[as.integer(x), ])
}

expit <- function(x) return(exp(x) / (1+exp(x)))