from topicpilot_api.orm.models import MarketDataSource, RawMarketObservation


def test_market_data_source_and_raw_observation_models_define_domain_boundary():
    assert MarketDataSource.__tablename__ == "market_data_sources"
    assert RawMarketObservation.__tablename__ == "raw_market_observations"
    assert "uq_market_data_sources_identity" in {
        c.name for c in MarketDataSource.__table__.constraints
    }
    assert "uq_raw_market_observations_source_hash" in {
        c.name for c in RawMarketObservation.__table__.constraints
    }
