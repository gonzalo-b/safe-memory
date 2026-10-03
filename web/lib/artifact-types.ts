import type {PhotoMetadata,SafeEvent} from './types';
export interface GallerySummary {id:string;type:'gallery';revision:number;title:string;layout:'grid'|'story';cover_asset_id:string|null;member_count:number;created_at:number;updated_at:number;private:true}
export interface GalleryMember {asset_id:string;revision:number;selected_revision:number;connection_id:string;media_type:PhotoMetadata['media_type'];capture_time:string|null;time_basis:PhotoMetadata['time_basis'];media_state:PhotoMetadata['media_state'];origin:string}
export interface Gallery extends GallerySummary {members:GalleryMember[];excluded_ids:string[];definition_version:string;lineage:{origin:string;trip_id:string|null;trip_revision:number|null;generation:string|null}}
export interface GalleryPage {artifacts:GallerySummary[];next_cursor:string|null;fixture:boolean}
export interface GalleryDebug {artifact_id:string;revision:number;definition_version:string;operations:(SafeEvent&{revision:number})[];bounds:{members:number;exclusions:number;revisions:number}}
export interface GalleryReceipt {artifact_id:string;revision:number;operation_id:string}
