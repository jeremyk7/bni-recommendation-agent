import argparse
import sys
from batch_processor import BatchProcessor

def main():
    parser = argparse.ArgumentParser(description="InRiver Product Image Batch Processor for Visual Search")
    
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=500,
        help="Number of products to process in this run (default: 500)"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Run without writing to Firestore or generating embeddings"
    )

    args = parser.parse_args()

    print("================================================")
    print("   Visual Product Search Batch Processor        ")
    print("================================================")
    if args.dry_run:
        print("!!! DRY RUN MODE ENABLED !!!")
    print(f"Target Batch Size: {args.batch_size}")
    print("------------------------------------------------")

    try:
        processor = BatchProcessor(dry_run=args.dry_run)
        summary = processor.run(total_limit=args.batch_size)
        
        if summary["total_failed"] > 0:
            print(f"Completed with {summary['total_failed']} errors.")
            sys.exit(0) # Still exit 0 if some finished? Or 1? Let's use 0 to avoid triggering retries in Job if it's partially successful.
        else:
            print("Successfully completed.")
            sys.exit(0)
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()