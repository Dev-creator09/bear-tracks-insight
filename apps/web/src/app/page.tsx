import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { CourseTable } from '@/components/course-table';

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="container flex flex-col items-center gap-4 py-16 md:py-24">
        <div className="flex max-w-[980px] flex-col items-center gap-2 text-center">
          <h1 className="text-3xl font-bold leading-tight tracking-tighter md:text-6xl lg:leading-[1.1]">
            Navigate Your Academic Journey with
            <span className="text-primary"> Bear Tracks</span>
          </h1>
          <p className="max-w-[750px] text-lg text-muted-foreground sm:text-xl">
            Discover courses, analyze student sentiment, and make informed decisions about
            your education. Powered by AI-driven insights and real student experiences.
          </p>
        </div>
        <div className="flex gap-4">
          <Button size="lg" asChild>
            <Link href="/courses">Browse Courses</Link>
          </Button>
          <Button size="lg" variant="outline" asChild>
            <Link href="/about">Learn More</Link>
          </Button>
        </div>
      </section>

      {/* Features Section */}
      <section className="container py-16 md:py-24 bg-muted/50">
        <div className="mx-auto flex max-w-[980px] flex-col items-center gap-4">
          <h2 className="text-3xl font-bold leading-tight tracking-tighter md:text-4xl">
            Features
          </h2>
          <div className="grid gap-6 md:grid-cols-3 mt-8">
            <div className="flex flex-col gap-2 p-6 bg-background rounded-lg border">
              <h3 className="text-xl font-bold">Course Discovery</h3>
              <p className="text-muted-foreground">
                Search and filter through thousands of courses with powerful search capabilities.
              </p>
            </div>
            <div className="flex flex-col gap-2 p-6 bg-background rounded-lg border">
              <h3 className="text-xl font-bold">Sentiment Analysis</h3>
              <p className="text-muted-foreground">
                AI-powered analysis of student reviews to understand course quality and difficulty.
              </p>
            </div>
            <div className="flex flex-col gap-2 p-6 bg-background rounded-lg border">
              <h3 className="text-xl font-bold">Prerequisite Tracking</h3>
              <p className="text-muted-foreground">
                Visualize course dependencies and plan your academic path effectively.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Sample Course Table */}
      <section className="container py-16 md:py-24">
        <div className="flex flex-col gap-4">
          <h2 className="text-3xl font-bold leading-tight tracking-tighter md:text-4xl">
            Popular Courses
          </h2>
          <CourseTable />
        </div>
      </section>
    </div>
  );
}
