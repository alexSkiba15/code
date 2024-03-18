import { inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, exhaustMap, interval, map, of, switchMap } from 'rxjs';
import { startWith } from 'rxjs/operators';

import { PriceDataByIndex } from '../../shared/models/stock';
import { PriceDataActions } from './market-prices.actions';
import { MarketPricesApiService } from './market-prices-api.service';

export const getMarketPrices = createEffect(
  (
    actions$: Actions = inject(Actions),
    marketPricesApiService: MarketPricesApiService = inject(MarketPricesApiService),
  ) => {
    const oneHour = 60 * 60 * 1000;
    return actions$.pipe(
      ofType(PriceDataActions.getAPIPriceData),
      switchMap(() => interval(oneHour).pipe(startWith(0))),
      exhaustMap(() =>
        marketPricesApiService.getTechnicalMarketIndicators().pipe(
          map((indicator: PriceDataByIndex) => {
            return PriceDataActions.bulkAddPriceData({
              priceData: [
                { ...indicator['^US10Y'], symbol: '^US10Y' },
                { ...indicator['^GSPC'], symbol: '^GSPC' },
                { ...indicator['^VIX'], symbol: '^VIX' },
              ],
            });
          }),
          catchError((error: { message: string }) => of(PriceDataActions.loadedFailure({ errorMsg: error.message }))),
        ),
      ),
    );
  },
  { functional: true },
);
