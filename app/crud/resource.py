# app/crud/resource.py
from sqlmodel import Session, select, func, and_
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.resource import Resource, ProjectResource
from app.models.project import Project
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceUpdate, ProjectResourceCreate, ProjectResourceUpdate

class ResourceCRUD:
    def create_resource(self, db: Session, resource_data: ResourceCreate) -> Resource:
        """Create a new resource."""
        resource = Resource(**resource_data.model_dump())
        db.add(resource)
        db.commit()
        db.refresh(resource)
        return resource
    
    def get_resource(self, db: Session, resource_id: int) -> Optional[Resource]:
        """Get resource by ID."""
        return db.get(Resource, resource_id)
    
    def get_resources(self, db: Session, skip: int = 0, limit: int = 100, resource_type: Optional[str] = None) -> List[Resource]:
        """Get resources with filtering."""
        query = select(Resource).where(Resource.is_active == True)
        
        if resource_type:
            query = query.where(Resource.type == resource_type)
        
        query = query.offset(skip).limit(limit).order_by(Resource.name)
        return db.exec(query).all()
    
    def update_resource(self, db: Session, resource_id: int, resource_data: ResourceUpdate) -> Optional[Resource]:
        """Update resource."""
        resource = db.get(Resource, resource_id)
        if not resource:
            return None
        
        update_data = resource_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(resource, field, value)
        
        resource.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(resource)
        return resource
    
    def get_resource_stats(self, db: Session) -> Dict[str, Any]:
        """Get resource statistics."""
        total_resources = db.exec(select(func.count(Resource.id)).where(Resource.is_active == True)).first()
        
        # Resources by type
        type_query = select(Resource.type, func.count(Resource.id)).where(Resource.is_active == True).group_by(Resource.type)
        type_data = db.exec(type_query).all()
        resources_by_type = {rtype: count for rtype, count in type_data}
        
        return {
            "total_resources": total_resources or 0,
            "resources_by_type": resources_by_type,
            "total_allocations": 0,  # Would need to calculate from ProjectResource
            "total_cost_allocated": 0.0,
            "utilization_rate": 0.0,
            "most_used_resources": []
        }

class ProjectResourceCRUD:
    def allocate_resource(self, db: Session, project_id: int, allocation_data: ProjectResourceCreate, user_id: int) -> ProjectResource:
        """Allocate resource to project."""
        allocation = ProjectResource(
            project_id=project_id,
            **allocation_data.model_dump(),
            allocated_by_id=user_id
        )
        db.add(allocation)
        db.commit()
        db.refresh(allocation)
        return allocation
    
    def get_project_resources(self, db: Session, project_id: int) -> List[Dict[str, Any]]:
        """Get resources allocated to a project."""
        query = (
            select(ProjectResource, Resource, User)
            .join(Resource, ProjectResource.resource_id == Resource.id)
            .outerjoin(User, ProjectResource.allocated_by_id == User.id)
            .where(ProjectResource.project_id == project_id)
        )
        results = db.exec(query).all()

        resources = []
        for allocation, resource, user in results:
            resources.append({
                "allocation": allocation,
                "resource": resource,
                "allocated_by": user
            })

        return resources

    def get_project_allocations(self, db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get paginated resource allocations for a project."""
        from app.schemas.resource import ResourceAllocation

        query = (
            select(ProjectResource, Resource, User)
            .join(Resource, ProjectResource.resource_id == Resource.id)
            .outerjoin(User, ProjectResource.allocated_by_id == User.id)
            .where(ProjectResource.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        results = db.exec(query).all()

        allocations = []
        for allocation, resource, user in results:
            allocations.append(ResourceAllocation(
                id=allocation.id,
                project_id=allocation.project_id,
                resource_id=allocation.resource_id,
                resource_name=resource.name,
                resource_type=resource.resource_type,
                quantity_allocated=allocation.quantity_allocated,
                quantity_used=allocation.quantity_used,
                allocation_date=allocation.allocation_date,
                allocated_by_id=allocation.allocated_by_id,
                allocated_by_name=user.name if user else None,
                created_at=allocation.created_at
            ))

        return allocations

    def count_project_allocations(self, db: Session, project_id: int) -> int:
        """Count resource allocations for a project."""
        query = select(func.count(ProjectResource.id)).where(ProjectResource.project_id == project_id)
        return db.exec(query).one()

# Create instances
resource_crud = ResourceCRUD()
project_resource_crud = ProjectResourceCRUD()