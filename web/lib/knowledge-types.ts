export interface KnowledgeFact {
  capture_time:string|null; capture_day:string|null; time_basis:string;
  location:{lat?:number;lon?:number;place?:string}; geography:{country_code?:string;country?:string;city_id?:string;city?:string};
  media_type:string|null; owner_presence:'owner'|'third_party'|'unknown'; continuous_presence:false;
  evidence?:{asset_id:string;revision:number;connection_id:string}; people?:{source_id:string;name:string}[];
}
export interface Coverage {scope:string;whole_library:false;indexed_records:number;unknown_time_records:number;located_records:number;first_observed_day:string|null;last_observed_day:string|null;unindexed_current_records:number;excluded_records:null}
export interface KnowledgeCatalog {capabilities:string[];definition_version:string;generation:string|null;coverage:Coverage;people:string;status:string}
export interface KnowledgeAnswer {capability:string;definition_version:string;generation:string|null;status:string;data:Record<string,unknown>[]|Record<string,number>;next_cursor:string|null;coverage:Coverage;time_basis:string;counting_rule:string;freshness:{built_at:number|null;stale:boolean;source_check:string};markdown:string;limitations:string[]}
export interface Trip {trip_id:string;revision:number;state:string;title:string;start:string|null;end:string|null;boundary_basis:string;kind:string;observed_start:string|null;observed_end:string|null;observed_day_count:number;unknown_time_records:number;observed_dates:string[];observed_dates_has_more:boolean;gaps:{start:string;end:string;status:string}[];gaps_complete:boolean;continuous_presence:false;owner_presence_confirmed:boolean;evidence_count:number;evidence:KnowledgeFact[];lineage:{parent_id:string;child_id:string;action:string}[];next_cursor?:string|null;definition_version:string}
export interface HistoricalArea {id:string;revision:number;label:string;lat:number;lon:number;radius_km:number;start:string;end:string;confirmed:0|1|boolean}
export interface KnowledgePage<T> {data:T[];next_cursor:string|null}
export interface CorrectionReceipt {operation_id:string;trip_ids:string[];revisions:Record<string,number>;status:'applied'}
