class CalculatedEstimatesWriterService(BaseCalculatedEstimatesWriterService):
    __slots__ = (
        'estimates_constructor',
        'report_archive_service',
        'report_estimate_helper_service',
        'report_reader',
    )

    def __init__(
        self,
        report_reader_service: ReportReaderService,
        report_archive_service: ReportArchivingService,
        report_estimate_helper_service: BaseReportEstimateHelperService,
        estimates_constructor_factory: EstimatesConstructorFactory,
    ) -> None:
        self.report_reader = report_reader_service
        self.report_archive_service = report_archive_service
        self.report_estimate_helper_service = report_estimate_helper_service
        self.estimates_constructor = estimates_constructor_factory(report_reader=self.report_reader)

    def update_calculated_estimates(self, stock_id: ObjectIdentity, analysts_on_stock: int) -> None:
        current_year = self.report_reader.get_last_actual_year(stock_id) + 1
        three_quarters_sum, last_management_date = self.report_estimate_helper_service.get_sum_three_quarters(
            stock_id, current_year
        )
        all_reports = self.report_reader.get_all_reports_for_stock(stock_id, year__gte=current_year)
        all_reports = self.report_estimate_helper_service.fill_obvious_gaps(
            all_reports, three_quarters_sum, last_management_report_date=last_management_date
        )
        buckets = self.report_reader.parse_reports_into_buckets(all_reports)
        previous_buckets = self.report_reader.parse_reports_into_buckets(
            self.report_archive_service.get_last_archived_buckets(stock_id)
        )
        result: list[CalculatedEstimate] = []

        for year, quarters in buckets.items():
            previous_quarters = previous_buckets.get(year, {})
            result.extend(
                self.estimates_constructor.construct_estimate_for_year(
                    stock_id,
                    year,
                    quarters=quarters,
                    previous_estimates=previous_quarters,
                    analysts_on_stock=analysts_on_stock,
                )
            )
        if result:
            CalculatedEstimate.objects(stock=stock_id).delete()
            CalculatedEstimate.objects.insert(result)

    def save_prev_values_on_calculated_estimates(self, stock_id: ObjectIdentity) -> None:
        db = get_db()
        db['calculated_estimate'].update_many(
            {'stock': stock_id, 'title': ESTIMATES_REVENUE_TITLE}, [{'$set': {'prev_value': '$value'}}]
        )
