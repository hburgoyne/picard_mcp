### Document Purpose
**PROCESSES.md:** Some usefull processes to document
- Useful processes and instructions for different workflows while developing, testing, maintaining the platform.
---

## Important Commands:

Rebuild Docker containers
```
docker-compose down --remove-orphans && docker image prune -f && docker-compose up --build -d
```

Run tests in Docker container
```
docker-compose exec web python manage.py test
```

---

Create new branch, then back to main (used to create 'deploy' branch):
```
git checkout main
git checkout -b deploy
git push -u origin deploy
git checkout main
```

Then merge 'main' into 'deploy' to deploy recent developments to Render:
```
git checkout deploy
git merge main
git push origin deploy
git checkout main
```


---
---