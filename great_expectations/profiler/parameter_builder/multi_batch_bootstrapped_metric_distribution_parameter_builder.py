import copy
from typing import Any, Dict, List, Optional, Union

from great_expectations import DataContext
from great_expectations.core.batch import BatchRequest
from great_expectations.core.domain_types import MetricDomainTypes
from great_expectations.profiler.domain_builder.domain import Domain
from great_expectations.profiler.parameter_builder.multi_batch_parameter_builder import (
    MultiBatchParameterBuilder,
)
from great_expectations.profiler.parameter_builder.parameter_container import (
    DOMAIN_KWARGS_PARAMETER_NAME,
    ParameterContainer,
    build_parameter_container,
)
from great_expectations.profiler.util import get_parameter_value
from great_expectations.validator.validation_graph import MetricConfiguration
from great_expectations.validator.validator import Validator


class MultiBatchBootstrappedMetricDistributionParameterBuilder(
    MultiBatchParameterBuilder
):
    """
    Defines the MultiBatchBootstrappedMetricDistributionParameterBuilder.

    Builds parameters from the p_values of the distribution of a metric observed from a set of batches identified in the
    batch_ids.
    """

    def __init__(
        self,
        parameter_name: str,
        validator: Validator,
        domain: Domain,
        batch_request: BatchRequest,
        metric_name: str,
        metric_value_kwargs: Union[str, dict],
        p_values: List[float],
        rule_variables: Optional[ParameterContainer] = None,
        rule_domain_parameters: Optional[Dict[str, ParameterContainer]] = None,
        data_context: Optional[DataContext] = None,
    ):
        """
        Create a MultiBatchBootstrappedMetricDistributionParameterBuilder.

        The ParameterBuilder will build parameters for the active domain from the rule.

        Args:
            parameter_name: the name of the parameter handled by this ParameterBuilder
            batch_request: BatchRequest elements that should be used to obtain additional batch_ids
            metric_name: metric from which to build the parameters
            metric_value_kwargs: value kwargs for the metric to be built
            p_values: the p_values for which to return metric value estimates
        """
        super().__init__(
            parameter_name=parameter_name,
            validator=validator,
            domain=domain,
            batch_request=batch_request,
            rule_variables=rule_variables,
            rule_domain_parameters=rule_domain_parameters,
            data_context=data_context,
        )

        self._metric_name = metric_name
        self._metric_value_kwargs = metric_value_kwargs
        self._p_values = p_values

    # TODO: <Alex>ALEX -- There is nothing about "p_values" in this implementation; moreover, "p_values" would apply only to certain values of the "metric_name" -- this needs to be elaborated.</Alex>
    def _build_parameters(
        self,
        batch_ids: Optional[List[str]] = None,
    ) -> ParameterContainer:
        samples = []
        # TODO: 20210426 AJB I think we need to handle not passing batch_ids here and everywhere else by processing all batches if `batch_ids is None`
        # TODO: <Alex>ALEX -- batch_id is not used -- so this is not miltibatch yet.  A potential approach is to compute metrics for the given domain for every batch (corresponding to the "batch_ids" list).  For this reason, the must-have requirement of including "batch_id" in "domain_kwargs" may need to be revised.</Alex>
        for batch_id in batch_ids:
            # TODO: <Alex>ALEX -- type overloading is generally a poor practice; the caller should decide on the type of "metric_domain_kwargs" and call this method accordingly.</Alex>
            # Using "__getitem__" (bracket) notation instead of "__getattr__" (dot) notation in order to insure the
            # compatibility of field names (e.g., "domain_kwargs") with user-facing syntax (as governed by the value of
            # the DOMAIN_KWARGS_PARAMETER_NAME constant, which may change, requiring the same change to the field name).
            metric_domain_kwargs: Union[
                str, Dict[str, Union[str, MetricDomainTypes, Dict[str, Any]]]
            ] = copy.deepcopy(self.domain[DOMAIN_KWARGS_PARAMETER_NAME])

            if (
                self._metric_value_kwargs
                and isinstance(self._metric_value_kwargs, str)
                and self._metric_value_kwargs.startswith("$")
            ):
                metric_value_kwargs = get_parameter_value(
                    fully_qualified_parameter_name=self._metric_value_kwargs,
                    domain=self.domain,
                    rule_variables=self.rule_variables,
                    rule_domain_parameters=self.rule_domain_parameters,
                )
            else:
                metric_value_kwargs = self._metric_value_kwargs

            samples.append(
                self.validator.get_metric(
                    metric=MetricConfiguration(
                        metric_name=self._metric_name,
                        metric_domain_kwargs=metric_domain_kwargs,
                        metric_value_kwargs=metric_value_kwargs,
                        metric_dependencies=None,
                    )
                )
            )

        parameter_values: Dict[str, Dict[str, Any]] = {
            f"$parameter.{self._metric_name}": {
                # TODO: Using the first sample for now, but this should be extended for handling multiple batches
                "value": samples[0],
                "details": None,
            },
        }
        return build_parameter_container(parameter_values=parameter_values)