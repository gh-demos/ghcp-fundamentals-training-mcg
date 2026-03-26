"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()

def test_remove():
    svc = ChromaService()
    svc.chroma_add_item("bar")
    assert svc.chroma_remove_item("bar") is True
    assert "bar" not in svc.chroma_list_items()
"""Tests for Chroma demo."""
import pytest
from app.chroma_service import ChromaService

def test_add_and_list():
    svc = ChromaService()
    svc.chroma_add_item("foo")
    assert "foo" in svc.chroma_list_items()
