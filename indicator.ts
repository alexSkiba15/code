export interface Indicator {
  idDimension?: [number, number[]];
  color?: string;
  config?: Record<string, string | number>;
  description: string;
  name?: string;
  onChart: boolean;
}

export class BasicIndicator implements Indicator {
  idDimension?: [number, number[]];
  color?: string;
  config: Record<string, string | number> | undefined;
  name: string | undefined;
  onChart: boolean = true;

  get description(): string {
    /**
     * @override it if config doesn't have a period
     */
    return `Period: ${this.config?.['period']}`;
  }
}

export class SimpleMovingAverage extends BasicIndicator {
  override config = {
    indicator: 'sma',
    period: 50,
    field: '',
    price_type: 'close',
  };

  override name = 'Simple Moving Average';

  override get description(): string {
    return `Period: ${this.config.period}, Type: ${this.config.price_type}`;
  }
}
