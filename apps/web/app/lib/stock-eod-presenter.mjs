export function isIntradayUpdateMode(updateMode) {
  return (updateMode ?? "").trim().toUpperCase() === "INTRADAY";
}

export function selectStockQuote(item) {
  if (item.isPreview === true) {
    return {
      source: "PREVIEW",
      price: item.price,
      change: null,
      changePct: item.changePct,
      volume: item.volume ?? null,
      dataStatus: "PREVIEW",
    };
  }

  if (isIntradayUpdateMode(item.updateMode)) {
    return {
      source: "INTRADAY_SOURCE",
      price: item.price,
      change: null,
      changePct: item.changePct,
      volume: item.volume ?? null,
      dataStatus: "UNAVAILABLE",
    };
  }

  if (!item.eod) {
    return {
      source: "UNAVAILABLE",
      price: null,
      change: null,
      changePct: null,
      volume: null,
      dataStatus: "UNAVAILABLE",
    };
  }

  return {
    source: "EOD_SOURCE",
    price: item.eod.close,
    change: item.eod.change,
    changePct: item.eod.changePct,
    volume: item.eod.volume,
    dataStatus: item.eod.dataStatus,
  };
}
