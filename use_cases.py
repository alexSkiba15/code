class RetrieveIntegrationUseCaseImpl(RetrieveIntegrationUseCase):
    def __init__(self, retrieval_service: AbstractRetrievalService) -> None:
        self.retrieval_service = retrieval_service

    async def __call__(
        self,
        integration_id: int,
        company_id: int,
    ) -> Integration:
        integration = (
            await (
                self.retrieval_service.get_integration_with_using_company_field(
                    company_id=company_id, integration_id=integration_id
                )
            )
        )

        if not integration:
            raise IntegrationNotFoundError(OBJECT_WAS_NOT_FOUND)

        return integration


class RetrieveIntegrationsUseCaseImpl(RetrieveIntegrationsUseCase):
    def __init__(
        self,
        retrieval_service: AbstractRetrievalService,
        ga4_client_factory: GA4APIClientFactory,
    ) -> None:
        self.retrieval_service = retrieval_service
        self.ga4_client_factory = ga4_client_factory

    async def __call__(
        self, company_id: int, add_is_refresh_token_valid_flag: bool | None = None
    ) -> list[IntegrationWithTokenStatus]:
        integrations = (
            await self.retrieval_service.get_integrations_with_using_company_field(
                company_id=company_id
            )
        )

        if add_is_refresh_token_valid_flag:
            result_integrations = []
            for integration in integrations:
                ga4_service = await self.ga4_client_factory(
                    refresh_token=integration.refresh_token,
                    property_id=integration.property_id,
                )
                result_integrations.append(
                    IntegrationWithTokenStatus(
                        is_refresh_token_valid=await ga4_service.credentials_are_valid,
                        **integration.dict(),
                    )
                )
        else:
            result_integrations = [
                IntegrationWithTokenStatus(**integration.dict())
                for integration in integrations
            ]
        return result_integrations


class SoftUpdateIntegrationUseCaseImpl(SoftUpdateIntegrationUseCase):
    def __init__(
        self,
        uow: UnitOfWork,
        retrieval_service: AbstractRetrievalService,
        integration_user_activity_generator: UserActivityGenerator[Integration],
        user_activity_service: AsyncUserActivityService,
        platform: str,
    ) -> None:
        self.uow = uow
        self.retrieval_service = retrieval_service
        self.integration_user_activity_generator = integration_user_activity_generator
        self.user_activity_service = user_activity_service
        self.platform = platform

    async def __call__(
        self, integration_id: int, name: str, user: AuthUser
    ) -> Integration:
        async with self.uow as uow:
            db_integration = await uow.integrations.get_or_raise(integration_id)

            if db_integration.company_id != user.company_id:
                raise IntegrationNotFoundError(OBJECT_WAS_NOT_FOUND)
            changes = Changes(new={"name": name}, old={"name": db_integration.name})
            db_integration.name = name

            await uow.integrations.add(db_integration)
            await uow.commit()

        user_activity = self.integration_user_activity_generator.make_user_activity(
            entity=db_integration,
            changes=changes,
            user=user,
            action=Action.update,
            platform=self.platform,
        )

        await self.user_activity_service.send(user_activity)

        return db_integration


class DeleteIntegrationUseCaseImpl(DeleteIntegrationUseCase):
    def __init__(
        self,
        uow: UnitOfWork,
        integration_user_activity_generator: UserActivityGenerator[Integration],
        user_activity_service: AsyncUserActivityService,
        platform: str,
    ) -> None:
        self.uow = uow
        self.integration_user_activity_generator = integration_user_activity_generator
        self.user_activity_service = user_activity_service
        self.platform = platform

    async def __call__(self, integration_id: int, user: AuthUser) -> None:
        async with self.uow as uow:
            integration = await uow.integrations.get_or_raise(integration_id)

            if integration.company_id != user.company_id:
                raise IntegrationNotFoundError(OBJECT_WAS_NOT_FOUND)

            await uow.integrations.delete(integration_id)

            await uow.commit()

        user_activity = self.integration_user_activity_generator.make_user_activity(
            entity=integration,
            changes=None,
            user=user,
            action=Action.delete,
            platform=self.platform,
        )
        await self.user_activity_service.send(user_activity)
