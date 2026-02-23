"""
Agent logic for the Technical Branding Assistant.
Handles the 'thinking' process when a file is in 02_Needs_Action.
Reads the topic, calls the search tool, and drafts a social media post and Simplified Study Guide.
"""

import os
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .tools.web_search import simple_search
from .config import NEEDS_ACTION_PATH, PENDING_APPROVAL_PATH
from .utils.file_handler import move_file
from .utils.metadata import add_yaml_frontmatter, update_yaml_frontmatter
from .watcher import update_file_status


def extract_topic_from_file(file_path: str) -> str:
    """
    Extract the topic from a file by reading its content.

    Args:
        file_path: Path to the file

    Returns:
        The topic extracted from the file
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read().strip()

        # If the file has YAML frontmatter, we might want to skip it
        # For now, just return the content as the topic
        # Remove YAML frontmatter if present
        if content.startswith('---'):
            # Find the end of YAML frontmatter
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        return content


def generate_social_post(topic: str, search_results: str) -> str:
    """
    Generate a social media post based on the topic and search results.

    Args:
        topic: The topic to write about
        search_results: Search results to base the post on

    Returns:
        Generated social media post content
    """
    social_post = f"""# {topic}: Key Insights & Trends

Based on my recent research into **{topic}**, here are the key insights and trends that professionals should be aware of:

## Overview
{search_results[:1000]}  # Using first 1000 chars of search results as overview

## Why This Matters
As technology continues to evolve rapidly, staying updated with the latest developments in {topic} is crucial for professionals in the field.

## Key Takeaways
1. [Add specific takeaway from search results]
2. [Add another takeaway from search results]
3. [Add final takeaway from search results]

## Looking Forward
The future of {topic} looks promising with ongoing innovations and developments. Professionals should consider how these trends might impact their work and career trajectory.

What are your thoughts on {topic}? Have you experienced similar trends in your work?

#TechInsights #{re.sub(r'\W+', '', topic)} #ProfessionalDevelopment #Innovation #Technology
"""
    return social_post


def generate_study_guide(topic: str, search_results: str) -> str:
    """
    Generate a simplified study guide based on the topic and search results.

    Args:
        topic: The topic to create a study guide for
        search_results: Search results to base the guide on

    Returns:
        Generated study guide content
    """
    study_guide = f"""# Simplified Study Guide: {topic}

## What is {topic}?
{search_results[:500]}  # Using first 500 chars of search results as introduction

## Key Concepts
1. [Concept 1 from search results]
2. [Concept 2 from search results]
3. [Concept 3 from search results]

## Practical Applications
- Application 1: [Description from search results]
- Application 2: [Description from search results]
- Application 3: [Description from search results]

## Resources for Further Learning
- Official Documentation: [Link from search results if available]
- Tutorials: [Links from search results if available]
- Community Forums: [Relevant communities from search results]

## Quick Tips
- Tip 1: [From search results]
- Tip 2: [From search results]
- Tip 3: [From search results]

## Common Pitfalls to Avoid
- Pitfall 1: [From search results]
- Pitfall 2: [From search results]

---
Study Guide created on: {datetime.now().strftime('%Y-%m-%d')}
Topic: {topic}
"""

    return study_guide


def process_needs_action_file(file_path: str) -> bool:
    """
    Process a file in the Needs Action folder:
    1. Extract the topic
    2. Search the web for information
    3. Generate LinkedIn post and study guide
    4. Save the results to a new file in Pending Approval
    5. Move the original file to Pending Approval

    Args:
        file_path: Path to the file in Needs Action folder

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Processing file: {file_path}")

        # Extract topic from the file
        topic = extract_topic_from_file(file_path)
        print(f"Extracted topic: {topic}")

        # Search the web for information about the topic
        print(f"Searching web for: {topic}")
        search_results = simple_search(topic)
        print("Search completed")

        # Generate social media post
        print("Generating social media post...")
        social_post = generate_social_post(topic, search_results)

        # Generate Simplified Study Guide
        print("Generating study guide...")
        study_guide = generate_study_guide(topic, search_results)

        # Create combined content with both the social post and study guide
        combined_content = f"""# Research Summary: {topic}

## Social Media Post Draft

{social_post}

---

## Simplified Study Guide

{study_guide}
"""

        # Create a new file in the Pending Approval folder with the results
        original_filename = Path(file_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{original_filename}_research_{timestamp}.md"
        new_file_path = PENDING_APPROVAL_PATH / new_filename

        print(f"Creating new file: {new_file_path}")
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(combined_content)

        # Add YAML frontmatter to the new file
        metadata = {
            'status': 'pending-approval',
            'original_topic': topic,
            'generated_on': datetime.now().isoformat(),
            'content_type': 'research_summary'
        }

        add_yaml_frontmatter(str(new_file_path), metadata)

        # Move the original file to Pending Approval as well (for reference)
        # But rename it to indicate it's the original topic
        original_ref_filename = f"{original_filename}_original_topic_{timestamp}.md"
        original_ref_path = PENDING_APPROVAL_PATH / original_ref_filename

        # Move the original file (instead of copying) to prevent re-processing
        move_file(file_path, str(original_ref_path))

        # Add metadata to the reference file
        ref_metadata = {
            'status': 'pending-approval',
            'purpose': 'original_topic_reference',
            'related_research_file': str(new_file_path.name)
        }

        add_yaml_frontmatter(str(original_ref_path), ref_metadata)

        # Update status of the new files to pending approval
        update_yaml_frontmatter(str(new_file_path), {'status': 'pending-approval'})
        update_yaml_frontmatter(str(original_ref_path), {'status': 'pending-approval'})

        print(f"Successfully processed and created files in Pending Approval folder")
        return True

    except Exception as e:
        print(f"Error processing needs action file {file_path}: {str(e)}")
        return False


def monitor_and_process_needs_action():
    """
    Monitor the Needs Action folder and process any files found there.
    This function can be called periodically to check for new files to process.
    """
    print("Checking for files in Needs Action folder...")

    # Look for all .md and .txt files in the Needs Action folder
    for file_path in NEEDS_ACTION_PATH.glob("*"):
        if file_path.suffix.lower() in ['.md', '.txt']:
            print(f"Found file to process: {file_path}")

            # Process the file
            if process_needs_action_file(str(file_path)):
                print(f"Successfully processed: {file_path}")
            else:
                print(f"Failed to process: {file_path}")


if __name__ == "__main__":
    # Example usage: process all files in the Needs Action folder
    monitor_and_process_needs_action()