# app/routers/blog.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer
from sqlmodel import Session
from typing import List, Optional

from app.database.engine import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.blog import BlogPostStatus
from app.crud.blog import blog_crud
from app.schemas.blog import (
    # Blog Post schemas
    BlogPostCreate, BlogPostUpdate, BlogPost, BlogPostSummary, BlogPostListResponse,
    # Category schemas
    CategoryCreate, CategoryUpdate, Category, CategoryListResponse,
    # Tag schemas
    TagCreate, TagUpdate, Tag, TagListResponse,
    # Author schema
    Author
)

router = APIRouter(
    prefix="/blog",
    tags=["blog"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


def require_admin(current_user: User) -> User:
    """Check if user is an admin."""
    if current_user.user_type.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action"
        )
    return current_user


# ========================================
# BLOG POST ENDPOINTS
# ========================================

@router.post("/posts", response_model=BlogPost, status_code=status.HTTP_201_CREATED)
def create_blog_post(
    post_data: BlogPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new blog post.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    try:
        post = blog_crud.create_blog_post(db, post_data, current_user.id)
        details = blog_crud.get_blog_post_with_details(db, post.id)

        # Build response with details
        response_data = {
            **post.model_dump(),
            "author": Author(**details["author"].model_dump()) if details["author"] else None,
            "categories": [Category(**c.model_dump(), post_count=0) for c in details["categories"]],
            "tags": [Tag(**t.model_dump(), post_count=0) for t in details["tags"]]
        }
        return BlogPost(**response_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create blog post: {str(e)}"
        )


@router.get("/posts", response_model=BlogPostListResponse)
def get_blog_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[BlogPostStatus] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    author_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = None
):
    """
    Get list of blog posts with filtering options.

    **Query Parameters**:
    - status: Filter by status (draft or published)
    - category: Filter by category slug
    - tag: Filter by tag slug
    - author_id: Filter by author ID
    - search: Search in title, excerpt, and content
    - skip: Number of posts to skip (pagination)
    - limit: Maximum number of posts to return (max 100)

    **Permissions**:
    - Published posts: Anyone (including unauthenticated)
    - Draft posts: Admin users only
    """
    try:
        # Determine if user can see drafts
        include_drafts = False
        if current_user and current_user.user_type.name == "admin":
            include_drafts = True

        posts, total = blog_crud.get_blog_posts(
            db,
            skip=skip,
            limit=limit,
            status=status,
            category=category,
            tag=tag,
            author_id=author_id,
            search=search,
            include_drafts=include_drafts
        )

        # Build response with details
        post_summaries = []
        for post in posts:
            details = blog_crud.get_blog_post_with_details(db, post.id)

            author_name = details["author"].name if details["author"] else None

            summary = BlogPostSummary(
                **post.model_dump(),
                author_name=author_name,
                categories=[Category(**c.model_dump(), post_count=0) for c in details["categories"]],
                tags=[Tag(**t.model_dump(), post_count=0) for t in details["tags"]]
            )
            post_summaries.append(summary)

        return BlogPostListResponse(
            items=post_summaries,
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blog posts: {str(e)}"
        )


@router.get("/posts/{post_id}", response_model=BlogPost)
def get_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = None
):
    """
    Get a single blog post by ID.

    **Permissions**:
    - Published posts: Anyone
    - Draft posts: Admin users only
    """
    post = blog_crud.get_blog_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Check permissions for draft posts
    if post.status == BlogPostStatus.draft:
        if not current_user or current_user.user_type.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found"
            )

    details = blog_crud.get_blog_post_with_details(db, post_id)

    response_data = {
        **post.model_dump(),
        "author": Author(**details["author"].model_dump()) if details["author"] else None,
        "categories": [Category(**c.model_dump(), post_count=0) for c in details["categories"]],
        "tags": [Tag(**t.model_dump(), post_count=0) for t in details["tags"]]
    }
    return BlogPost(**response_data)


@router.get("/posts/by-slug/{slug}", response_model=BlogPost)
def get_blog_post_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = None
):
    """
    Get a single blog post by slug.

    **Permissions**:
    - Published posts: Anyone
    - Draft posts: Admin users only
    """
    post = blog_crud.get_blog_post_by_slug(db, slug)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Check permissions for draft posts
    if post.status == BlogPostStatus.draft:
        if not current_user or current_user.user_type.name != "admin":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Blog post not found"
            )

    details = blog_crud.get_blog_post_with_details(db, post.id)

    response_data = {
        **post.model_dump(),
        "author": Author(**details["author"].model_dump()) if details["author"] else None,
        "categories": [Category(**c.model_dump(), post_count=0) for c in details["categories"]],
        "tags": [Tag(**t.model_dump(), post_count=0) for t in details["tags"]]
    }
    return BlogPost(**response_data)


@router.put("/posts/{post_id}", response_model=BlogPost)
def update_blog_post(
    post_id: int,
    post_data: BlogPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a blog post.

    **Permissions**: Admin only (must be post author)
    """
    require_admin(current_user)

    post = blog_crud.get_blog_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Check if user is the author
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own blog posts"
        )

    try:
        updated_post = blog_crud.update_blog_post(db, post_id, post_data)
        details = blog_crud.get_blog_post_with_details(db, post_id)

        response_data = {
            **updated_post.model_dump(),
            "author": Author(**details["author"].model_dump()) if details["author"] else None,
            "categories": [Category(**c.model_dump(), post_count=0) for c in details["categories"]],
            "tags": [Tag(**t.model_dump(), post_count=0) for t in details["tags"]]
        }
        return BlogPost(**response_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update blog post: {str(e)}"
        )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a blog post.

    **Permissions**: Admin only (must be post author)
    """
    require_admin(current_user)

    post = blog_crud.get_blog_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Check if user is the author
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own blog posts"
        )

    success = blog_crud.delete_blog_post(db, post_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete blog post"
        )


@router.post("/posts/{post_id}/publish", response_model=BlogPost)
def publish_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publish a draft blog post.

    **Permissions**: Admin only (must be post author)
    """
    require_admin(current_user)

    post = blog_crud.get_blog_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Check if user is the author
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own blog posts"
        )

    published_post = blog_crud.publish_blog_post(db, post_id)
    details = blog_crud.get_blog_post_with_details(db, post_id)

    response_data = {
        **published_post.model_dump(),
        "author": Author(**details["author"].model_dump()) if details["author"] else None,
        "categories": [Category(**c.model_dump(), post_count=0) for c in details["categories"]],
        "tags": [Tag(**t.model_dump(), post_count=0) for t in details["tags"]]
    }
    return BlogPost(**response_data)


@router.post("/posts/{post_id}/unpublish", response_model=BlogPost)
def unpublish_blog_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unpublish a blog post (revert to draft).

    **Permissions**: Admin only (must be post author)
    """
    require_admin(current_user)

    post = blog_crud.get_blog_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog post not found"
        )

    # Check if user is the author
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unpublish your own blog posts"
        )

    unpublished_post = blog_crud.unpublish_blog_post(db, post_id)
    details = blog_crud.get_blog_post_with_details(db, post_id)

    response_data = {
        **unpublished_post.model_dump(),
        "author": Author(**details["author"].model_dump()) if details["author"] else None,
        "categories": [Category(**c.model_dump(), post_count=0) for c in details["categories"]],
        "tags": [Tag(**t.model_dump(), post_count=0) for t in details["tags"]]
    }
    return BlogPost(**response_data)


# ========================================
# CATEGORY ENDPOINTS
# ========================================

@router.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new category.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    try:
        category = blog_crud.create_category(db, category_data)
        post_count = blog_crud.get_category_post_count(db, category.id)
        return Category(**category.model_dump(), post_count=post_count)

    except Exception as e:
        # Check for unique constraint violation
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {str(e)}"
        )


@router.get("/categories", response_model=CategoryListResponse)
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get list of all categories.

    **Permissions**: Public (no authentication required)
    """
    try:
        categories, total = blog_crud.get_categories(db, skip=skip, limit=limit)

        # Add post counts
        categories_with_counts = []
        for category in categories:
            post_count = blog_crud.get_category_post_count(db, category.id)
            categories_with_counts.append(
                Category(**category.model_dump(), post_count=post_count)
            )

        return CategoryListResponse(
            items=categories_with_counts,
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )


@router.get("/categories/{category_id}", response_model=Category)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single category by ID.

    **Permissions**: Public
    """
    category = blog_crud.get_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    post_count = blog_crud.get_category_post_count(db, category_id)
    return Category(**category.model_dump(), post_count=post_count)


@router.get("/categories/by-slug/{slug}", response_model=Category)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get a single category by slug.

    **Permissions**: Public
    """
    category = blog_crud.get_category_by_slug(db, slug)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    post_count = blog_crud.get_category_post_count(db, category.id)
    return Category(**category.model_dump(), post_count=post_count)


@router.put("/categories/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a category.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    try:
        updated_category = blog_crud.update_category(db, category_id, category_data)
        if not updated_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        post_count = blog_crud.get_category_post_count(db, category_id)
        return Category(**updated_category.model_dump(), post_count=post_count)

    except HTTPException:
        raise
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A category with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update category: {str(e)}"
        )


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a category.

    **Permissions**: Admin only
    **Note**: Cannot delete a category that has associated blog posts
    """
    require_admin(current_user)

    success = blog_crud.delete_category(db, category_id)
    if not success:
        # Check if category exists
        category = blog_crud.get_category(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete category that has associated blog posts"
            )


# ========================================
# TAG ENDPOINTS
# ========================================

@router.post("/tags", response_model=Tag, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new tag.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    try:
        tag = blog_crud.create_tag(db, tag_data)
        post_count = blog_crud.get_tag_post_count(db, tag.id)
        return Tag(**tag.model_dump(), post_count=post_count)

    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A tag with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tag: {str(e)}"
        )


@router.get("/tags", response_model=TagListResponse)
def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get list of all tags.

    **Permissions**: Public (no authentication required)
    """
    try:
        tags, total = blog_crud.get_tags(db, skip=skip, limit=limit)

        # Add post counts
        tags_with_counts = []
        for tag in tags:
            post_count = blog_crud.get_tag_post_count(db, tag.id)
            tags_with_counts.append(
                Tag(**tag.model_dump(), post_count=post_count)
            )

        return TagListResponse(
            items=tags_with_counts,
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tags: {str(e)}"
        )


@router.get("/tags/{tag_id}", response_model=Tag)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single tag by ID.

    **Permissions**: Public
    """
    tag = blog_crud.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    post_count = blog_crud.get_tag_post_count(db, tag_id)
    return Tag(**tag.model_dump(), post_count=post_count)


@router.get("/tags/by-slug/{slug}", response_model=Tag)
def get_tag_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get a single tag by slug.

    **Permissions**: Public
    """
    tag = blog_crud.get_tag_by_slug(db, slug)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    post_count = blog_crud.get_tag_post_count(db, tag.id)
    return Tag(**tag.model_dump(), post_count=post_count)


@router.put("/tags/{tag_id}", response_model=Tag)
def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a tag.

    **Permissions**: Admin only
    """
    require_admin(current_user)

    try:
        updated_tag = blog_crud.update_tag(db, tag_id, tag_data)
        if not updated_tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tag not found"
            )

        post_count = blog_crud.get_tag_post_count(db, tag_id)
        return Tag(**updated_tag.model_dump(), post_count=post_count)

    except HTTPException:
        raise
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A tag with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tag: {str(e)}"
        )


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a tag.

    **Permissions**: Admin only
    **Note**: This will remove the tag from all associated blog posts
    """
    require_admin(current_user)

    success = blog_crud.delete_tag(db, tag_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
