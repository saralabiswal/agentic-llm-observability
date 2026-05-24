/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
import type { ReactNode } from "react";

export type DataTableColumn<T> = {
  key: keyof T;
  label: string;
  render?: (row: T) => ReactNode;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  rows: T[];
  onRowClick?: (row: T) => void;
};

export function DataTable<T extends Record<string, ReactNode>>({ columns, rows, onRowClick }: DataTableProps<T>) {
  return (
    <div className="data-table-wrap">
      <table className="data-table">
        <thead className="table-head">
          <tr>
            {columns.map((column) => (
              <th className="table-cell" key={String(column.key)}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr className="table-row" key={index} onClick={() => onRowClick?.(row)}>
              {columns.map((column) => (
                <td className="table-cell" key={String(column.key)}>
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
