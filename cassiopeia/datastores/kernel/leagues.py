from typing import Type, TypeVar, MutableMapping, Any, Iterable, Generator

from datapipelines import DataSource, PipelineContext, Query, NotFoundError, validate_query
from .common import KernelSource, APINotFoundError
from ...data import Platform, Queue, Tier, Division
from ...dto.league import LeaguesListDto, ChallengerLeagueListDto, MasterLeagueListDto,GrandmasterLeagueListDto, LeaguePositionsDto, LeagueListDto, PaginatedLeaguesListDto
from ..uniquekeys import convert_region_to_platform

T = TypeVar("T")


class LeaguesAPI(KernelSource):
    @DataSource.dispatch
    def get(self, type: Type[T], query: MutableMapping[str, Any], context: PipelineContext = None) -> T:
        pass

    @DataSource.dispatch
    def get_many(self, type: Type[T], query: MutableMapping[str, Any], context: PipelineContext = None) -> Iterable[T]:
        pass

    _validate_get_paginated_leagues_list_query = Query. \
        has("queue").as_(Queue).also. \
        has("tier").as_(Tier).also. \
        has("division").as_(Division).also. \
        has("page").as_(int).also. \
        has("platform").as_(Platform)

    @get.register(PaginatedLeaguesListDto)
    @validate_query(_validate_get_paginated_leagues_list_query, convert_region_to_platform)
    def get_league_entries_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> PaginatedLeaguesListDto:
        parameters = {"platform": query["platform"].value}
        endpoint = "lol/league/v4/entries/{queue}/{tier}/{division}/{page}".format(
            queue=query["queue"].value,
            tier=query["tier"].value,
            division=query["division"].value,
            page=query["page"]
        )
        try:
            data = self._get(endpoint=endpoint, parameters=parameters)
        except APINotFoundError:
            data = []
        region = query["platform"].region.value
        for entry in data:
            entry["region"] = region
        return PaginatedLeaguesListDto(entries=data, page=query["page"], region=query["region"].value, queue=query["queue"].value, tier=query["tier"].value, division=query["division"].value)

    # Leagues

    _validate_get_leagues_query = Query. \
        has("id").as_(str).also. \
        has("platform").as_(Platform)

    @get.register(LeagueListDto)
    @validate_query(_validate_get_leagues_query, convert_region_to_platform)
    def get_leagues_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> LeagueListDto:
        parameters = {"platform": query["platform"].value}
        endpoint = "lol/league/v4/leagues/{leagueId}".format(leagueId=query["id"])
        try:
            data = self._get(endpoint=endpoint, parameters=parameters)
        except APINotFoundError as error:
            raise NotFoundError(str(error)) from error

        data["region"] = query["platform"].region.value
        for entry in data["entries"]:
            entry["region"] = data["region"]
            entry["tier"] = data["tier"]
        return LeagueListDto(data)

    _validate_get_many_leagues_by_summoner_query = Query. \
        has("summoner.ids").as_(Iterable).also. \
        has("platform").as_(Platform)

    @get_many.register(LeaguesListDto)
    @validate_query(_validate_get_many_leagues_by_summoner_query, convert_region_to_platform)
    def get_many_leagues_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> Generator[LeaguesListDto, None, None]:
        def generator():
            parameters = {"platform": query["platform"].value}
            for id in query["summoner.ids"]:
                endpoint = "lol/league/v4/leagues/by-summoner/{summonerId}".format(summonerId=id)
                try:
                    data = self._get(endpoint=endpoint, parameters=parameters)
                except APINotFoundError as error:
                    raise NotFoundError(str(error)) from error

                data["region"] = query["platform"].region.value
                data["summonerId"] = id
                for entry in data["entries"]:
                    entry["region"] = data["region"]
                yield LeaguesListDto(data)

        return generator()

    _validate_get_many_leagues_query = Query. \
        has("ids").as_(Iterable).also. \
        has("platform").as_(Platform)

    @get_many.register(LeagueListDto)
    @validate_query(_validate_get_many_leagues_query, convert_region_to_platform)
    def get_many_leagues_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> Generator[LeagueListDto, None, None]:
        def generator():
            parameters = {"platform": query["platform"].value}
            for id in query["ids"]:
                endpoint = "lol/league/v4/leagues/{leagueId}".format(leagueId=id)
                try:
                    data = self._get(endpoint=endpoint, parameters=parameters)
                except APINotFoundError as error:
                    raise NotFoundError(str(error)) from error

                data = {"leagues": data}
                data["region"] = query["platform"].region.value
                for league in data["leagues"]:
                    league["region"] = data["region"]
                    for entry in league["entries"]:
                        entry["region"] = data["region"]
                yield LeagueListDto(data)

        return generator()


    _validate_get_challenger_league_query = Query. \
        has("queue").as_(Queue).also. \
        has("platform").as_(Platform)

    @get.register(ChallengerLeagueListDto)
    @validate_query(_validate_get_challenger_league_query, convert_region_to_platform)
    def get_challenger_league_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> ChallengerLeagueListDto:
        parameters = {"platform": query["platform"].value}
        endpoint = "lol/league/v4/challengerleagues/by-queue/{queueName}".format(queueName=query["queue"].value)
        try:
            data = self._get(endpoint=endpoint, parameters=parameters)
        except APINotFoundError as error:
            raise NotFoundError(str(error)) from error

        data["region"] = query["platform"].region.value
        data["queue"] = query["queue"].value
        for entry in data["entries"]:
            entry["region"] = data["region"]
        return ChallengerLeagueListDto(data)

    _validate_get_many_challenger_league_query = Query. \
        has("queues").as_(Iterable).also. \
        has("platform").as_(Platform)

    @get_many.register(ChallengerLeagueListDto)
    @validate_query(_validate_get_many_challenger_league_query, convert_region_to_platform)
    def get_challenger_leagues_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> Generator[ChallengerLeagueListDto, None, None]:
        def generator():
            parameters = {"platform": query["platform"].value}
            for queue in query["queues"]:
                endpoint = "lol/league/v4/challengerleagues/by-queue/{queueName}".format(queueName=queue.value)
                try:
                    data = self._get(endpoint=endpoint, parameters=parameters)
                except APINotFoundError as error:
                    raise NotFoundError(str(error)) from error

                data = {"leagues": data}
                data["region"] = query["platform"].region.value
                data["queue"] = queue.value
                for entry in data["entries"]:
                    entry["region"] = data["region"]
                yield ChallengerLeagueListDto(data)

        return generator()

    _validate_get_grandmaster_league_query = Query. \
        has("queue").as_(Queue).also. \
        has("platform").as_(Platform)

    @get.register(GrandmasterLeagueListDto)
    @validate_query(_validate_get_grandmaster_league_query, convert_region_to_platform)
    def get_grandmaster_league_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> GrandmasterLeagueListDto:
        parameters = {"platform": query["platform"].value}
        endpoint = "lol/league/v4/grandmasterleagues/by-queue/{queueName}".format(queueName=query["queue"].value)
        try:
            data = self._get(endpoint=endpoint, parameters=parameters)
        except APINotFoundError as error:
            raise NotFoundError(str(error)) from error

        data["region"] = query["platform"].region.value
        data["queue"] = query["queue"].value
        for entry in data["entries"]:
            entry["region"] = data["region"]
        return GrandmasterLeagueListDto(data)

    _validate_get_many_grandmaster_league_query = Query. \
        has("queues").as_(Iterable).also. \
        has("platform").as_(Platform)

    @get_many.register(GrandmasterLeagueListDto)
    @validate_query(_validate_get_many_grandmaster_league_query, convert_region_to_platform)
    def get_grandmaster_leagues_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> Generator[GrandmasterLeagueListDto, None, None]:
        def generator():
            parameters = {"platform": query["platform"].value}
            for queue in query["queues"]:
                endpoint = "lol/league/v4/grandmasterleagues/by-queue/{queueName}".format(queueName=queue.value)
                try:
                    data = self._get(endpoint=endpoint, parameters=parameters)
                except APINotFoundError as error:
                    raise NotFoundError(str(error)) from error

                data = {"leagues": data}
                data["region"] = query["platform"].region.value
                data["queue"] = queue.value
                for entry in data["entries"]:
                    entry["region"] = data["region"]
                yield GrandmasterLeagueListDto(data)

        return generator()


    _validate_get_master_league_query = Query. \
        has("queue").as_(Queue).also. \
        has("platform").as_(Platform)

    @get.register(MasterLeagueListDto)
    @validate_query(_validate_get_master_league_query, convert_region_to_platform)
    def get_master_league_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> MasterLeagueListDto:
        parameters = {"platform": query["platform"].value}
        endpoint = "lol/league/v4/masterleagues/by-queue/{queueName}".format(queueName=query["queue"].value)
        try:
            data = self._get(endpoint=endpoint, parameters=parameters)
        except APINotFoundError as error:
            raise NotFoundError(str(error)) from error

        data["region"] = query["platform"].region.value
        data["queue"] = query["queue"].value
        for entry in data["entries"]:
            entry["region"] = data["region"]
        return MasterLeagueListDto(data)

    _validate_get_many_master_league_query = Query. \
        has("queues").as_(Iterable).also. \
        has("platform").as_(Platform)

    @get_many.register(MasterLeagueListDto)
    @validate_query(_validate_get_many_master_league_query, convert_region_to_platform)
    def get_master_leagues_list(self, query: MutableMapping[str, Any], context: PipelineContext = None) -> Generator[MasterLeagueListDto, None, None]:
        def generator():
            parameters = {"platform": query["platform"].value}
            for queue in query["queues"]:
                endpoint = "lol/league/v4/masterleagues/by-queue/{queueName}".format(queueName=queue.value)
                try:
                    data = self._get(endpoint=endpoint, parameters=parameters)
                except APINotFoundError as error:
                    raise NotFoundError(str(error)) from error

                data = {"leagues": data}
                data["region"] = query["platform"].region.value
                data["queue"] = queue.value
                for entry in data["entries"]:
                    entry["region"] = data["region"]
                yield MasterLeagueListDto(data)

        return generator()
