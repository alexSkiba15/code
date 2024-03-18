import { NgFor } from '@angular/common';
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';

import { FinancialInfo, FinancialsTable } from '../shared/interfaces';
import { FormatNumberPipe } from '../shared/pipes';

interface ReformedFinancials {
  title: string;
  [key: string]: number | string;
}

@Component({
  selector: 'app-financial-report',
  templateUrl: './financial-report.component.html',
  styleUrls: ['./financial-report.component.css'],
  standalone: true,
  imports: [MatTableModule, NgFor, FormatNumberPipe],
})
export class FinancialReportComponent implements OnChanges {
  @Input()
  years?: number[];

  @Input()
  financials: FinancialsTable = {};

  reformedFinancials: ReformedFinancials[] = [];
  dataSource = new MatTableDataSource<ReformedFinancials>();
  columnsToDisplay: string[] = [];

  ngOnChanges(changes: SimpleChanges): void {
    if (changes?.['financials'] && this.financials) {
      Object.entries(this.financials).forEach(
        ([title, years]: [string, { values: { [key: number]: FinancialInfo } }]) => {
          const rf: ReformedFinancials = {
            title,
          };
          const values = years.values ?? years;
          let i = 0;
          Object.values(values).forEach((dataPerYear: FinancialInfo) => {
            i += 1;
            rf[`value${i}`] = dataPerYear.value;
          });
          this.reformedFinancials.push(rf);
        },
      );

      this.columnsToDisplay = Array.from({ length: this.years?.length ?? 0 }, (_, key) => `value${key + 1}`);
      this.columnsToDisplay.splice(0, 0, 'title');
      this.dataSource.data = this.reformedFinancials;
    }
  }
}
