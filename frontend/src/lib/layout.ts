export type Positioned={shelf_number?:number;position?:number}
export function physicalOrder<T extends Positioned>(rows:T[]):T[]{return[...rows].sort((a,b)=>(a.shelf_number||1)-(b.shelf_number||1)||(a.position||0)-(b.position||0))}
export function groupByShelf<T extends Positioned>(rows:T[]):[string,T[]][]{const groups=physicalOrder(rows).reduce((all,row)=>{const shelf=String(row.shelf_number||1);(all[shelf]??=[]).push(row);return all},{} as Record<string,T[]>);return Object.entries(groups)}
